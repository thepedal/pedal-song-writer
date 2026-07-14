#!/usr/bin/env python3
"""Build the `bench_depth_NN` benchmark songs -- deterministic DAG-depth test cases.

PR #130 replaces the per-DAG-level barrier loop with ONE barrier per buffer, so the
saving is `depth - 1` barriers per buffer: it scales with graph DEPTH and nothing else.
det_grid_08x04's cone is only 4 levels deep (it measured exactly 4.00 barriers/buffer on
the wave path), so it is a modest case. These songs vary depth, holding all else fixed.

    SH101 -+-> G0_00 -> G0_01 -> ... -> G0_(NN-1) -+-> Master
           +-> G1_00 -> G1_01 -> ... -> G1_(NN-1) -+
           |     :                                 |
           +-> G7_00 -> G7_01 -> ... -> G7_(NN-1) -+

  * WIDTH fixed at 8 = AudioThreads, so every level is fully parallel and thread
    starvation never becomes a variable. (A 4-wide song on 8 threads would idle half
    the workers and confound depth with parallelism.)
  * DEPTH is the only thing that varies between the songs.
  * Each gain takes exactly ONE input -- far under Pedal Gain Multi's 6-input cap.
  * Cone = SH101 (alone on its level -> run inline -> no barrier) + NN gain levels, so
    the wave path should report barriersPerBuffer == NN exactly. That is a free
    self-check: if it doesn't, this topology model is wrong and we learn it at once.

Deterministic: no MIDI, no LFOs, no humanize. Gain Multi is stateless. SH101 retriggers
one note per bar -- a single held note would decay toward silence and risk denormal
stalls in the gain chain, which is noise in the measurement, not signal.

    python3 src/build_bench_depth.py         # depths 4, 8, 16
    python3 src/build_bench_depth.py 8       # just depth 8
"""
import os
import sys

from rebuzz import (
    note_value as nv,
    build_blob_cols, build_blob_mt,
    read, machine_blocks, name_of, lib_of,
    pattern_xml, set_patterns, set_data, set_track_count, set_position,
    set_name, set_editor, set_param,
    assert_no_overlap, assert_valid,
    machines_xml, connections_xml_multi, sequences_xml_multi,
    splice, set_loop_song_end, set_tempo, rename_song, clear_held_notes, write_bmxml,
)
from rebuzz.blocks import set_input_tracks   # not re-exported from the package

_HERE  = os.path.dirname(os.path.abspath(__file__))
REFS   = os.environ.get("REBUZZ_REFS")   or os.path.join(_HERE, "..", "refs")
OUTDIR = os.environ.get("REBUZZ_OUTDIR") or os.path.join(_HERE, "..", "songs")
def ref(n): return os.path.join(REFS, n)

WIDTH = 8                 # = AudioThreads. Read the note above before changing.
BPM, TPB = 120, 4
BAR   = TPB * 4           # 16 rows/bar (4/4)
BARS  = 16
TOTAL = BARS * BAR        # 256 rows ~= 32 s at 120 BPM

SRC_NOTE       = nv(3, 0)   # C-3, retriggered every bar
SH101_NOTE_COL = 25         # Pedal SH101: monophonic, note column 25
UNITY          = 16384


def build(depth):
    syn = read(ref('synthref.bmxml'))    # skeleton: Master + 4 synths + editors pe1..pe5
    gan = read(ref('gainref.bmxml'))     # Pedal Gain Multi template (saved with 4 inputs)
    chd = read(ref('chordref.bmxml'))    # Modern Pattern Editor template

    GAINMULTI_TMPL = next(b for b in machine_blocks(gan) if lib_of(b) == 'Pedal Gain Multi')
    MPE_TMPL = next(b for b in machine_blocks(chd)
                    if lib_of(b) == 'Modern Pattern Editor' and name_of(b) == '_x0001_pe3')

    PAT = pattern_xml('00', TOTAL)
    final_blocks, seqs, conns, editors = [], [], [], []

    # The skeleton carries four synths; keep ONLY the SH101 and drop Lead/Pad/Comp --
    # a benchmark wants one deterministic source, not a band. Its skeleton name 'Bass'
    # is kept deliberately: renaming a skeleton block is a mutation we don't need.
    SRC, SRC_EDITOR = 'Bass', '_x0001_pe2'

    for b in machine_blocks(syn):
        lib, nm = lib_of(b), name_of(b)
        if lib == 'Master':
            mb = b.replace('<Patterns />', PAT, 1)
            mb = set_position(mb, 0.0, 0.30 * depth + 0.45)   # park clear of the gain grid
            final_blocks.append(mb)
            seqs.append(('Master', [(0, TOTAL, '00')]))
        elif nm == '_x0001_pe1':                              # Master's editor = tempo
            final_blocks.append(set_data(b, build_blob_cols(
                'Master', '00', 3, {1: [(0, BPM)], 2: [(0, TPB)]})))
            editors.append('_x0001_pe1')
        elif lib == 'Pedal SH101':
            sb = set_position(set_track_count(set_patterns(b, PAT), 1), 0.0, -0.55)
            final_blocks.append(sb)
            seqs.append((SRC, [(0, TOTAL, '00')]))
        elif nm == SRC_EDITOR:                                # one note-on per bar
            ev = {(0, SH101_NOTE_COL): [(bar * BAR, SRC_NOTE) for bar in range(BARS)]}
            final_blocks.append(set_data(b, build_blob_mt(
                SRC, '00', [SH101_NOTE_COL], 1, ev)))
            editors.append(SRC_EDITOR)
        # Lead / Pad / Comp and editors pe3..pe5 are deliberately dropped.

    ed_n = 10                                   # gain editors start clear of pe1..pe5
    grid = [[None] * depth for _ in range(WIDTH)]

    for chain in range(WIDTH):
        for level in range(depth):
            gname = 'G%d_%02d' % (chain, level)
            ename = '_x0001_pe%d' % ed_n
            ed_n += 1

            gb = set_name(GAINMULTI_TMPL, 'PGainMul', gname)
            gb = set_patterns(set_editor(gb, ename), PAT)
            # MANDATORY: gainref's template is saved with 4 input channels (LastCall's
            # two buses both happen to take 4 inputs, so it never had to resize). Our
            # chain gains take exactly ONE input; the Input group's TrackCount must
            # equal the connection count or the per-input fader array is wrong.
            gb = set_input_tracks(gb, 1)
            gb = set_param(gb, 'Amp', UNITY)
            gb = set_position(gb, -1.40 + chain * 0.40, 0.30 * level)

            final_blocks.append(gb)
            final_blocks.append(set_data(set_name(MPE_TMPL, '_x0001_pe3', ename),
                                         build_blob_cols(gname, '00', 8, {})))
            seqs.append((gname, [(0, TOTAL, '00')]))
            editors.append(ename)
            grid[chain][level] = gname

    for chain in range(WIDTH):
        conns.append((SRC, grid[chain][0], UNITY, UNITY, 0, 0))          # source -> head
        for level in range(depth - 1):
            conns.append((grid[chain][level], grid[chain][level+1], UNITY, UNITY, 0, 0))
        conns.append(grid[chain][depth - 1])                             # tail -> Master
    conns.extend(editors)                                                # editors -> Master

    out = splice(syn, machines_xml(final_blocks),
                 connections_xml_multi(conns), sequences_xml_multi(seqs))
    out = set_loop_song_end(out, TOTAL)
    out = set_tempo(out, BPM, TPB)
    out = rename_song(out, 'synthref', 'bench_depth_%02d' % depth)
    out = clear_held_notes(out)
    assert_no_overlap(out)
    assert_valid(out)

    path = os.path.join(OUTDIR, 'bench_depth_%02d.bmxml' % depth)
    write_bmxml(path, out)
    print('WROTE %s' % path)
    print('   width=%d depth=%d  gains=%d  audio connections=%d  machines=%d'
          % (WIDTH, depth, WIDTH*depth, WIDTH*depth + WIDTH,
             2 + 2 + 2*WIDTH*depth))
    print('   EXPECT on the wave path: barriersPerBuffer == %.2f' % depth)
    return path


if __name__ == '__main__':
    for d in [int(a) for a in sys.argv[1:]] or [4, 8, 16]:
        build(d)
