#!/usr/bin/env python3
"""Build the `bench_host_NN` benchmark songs -- deterministic HOST-LOOP scaling tests.

Companion to build_bench_depth.py. Where bench_depth varies DAG *depth* to measure the
per-barrier dispatch saving (PR #130), bench_host varies song *size* to measure the three
per-chunk host-side loops that run on the audio thread OUTSIDE the parallel dispatch region
and scale with total song content, not with what's playing:

    UpdatePatternColumnEvents  (colEv)  -- one PlayPatternColumnEvents per sequence placement
    CallTick                   (tick)   -- walks the full machine list (twice) per chunk
    UpdatePatternPositions     (patPos) -- clears PlayPosition on every pattern of every machine

These are the "Tier 1" targets from the 2026-07-15 static read of the merged tip. On amanita-
scale content the phase probe put them at ~11% of the fill (mostly tick); this family answers
whether that grows with size, and the phase-probe columns attribute the slope of each loop
independently. If the loops stay flat/small as size grows, Tier 1 is low-value and we learn it
cheaply; if one dominates, the probe hands us the fix order.

    SH101 -+-> G0_00 -> G0_01 -> G0_02 -+-> Master     (DEPTH = 3, constant)
           +-> G1_00 -> G1_01 -> G1_02 -+
           |     :                      |
           +-> G(W-1)_00 -> ...      ---+               (WIDTH = NN, the size scalar)

  * DEPTH fixed at 3 and shallow ON PURPOSE. We are NOT re-measuring the barrier saving
    (bench_depth did that). Holding depth constant holds the dispatch cost per buffer ~constant
    (depth-1 = 2 barriers/buffer at every size) while machine/pattern/placement count grows, so
    the host-loop columns move and the dispatch column does not -- clean separation.
  * WIDTH = NN is the ONLY thing that varies. Every host-loop driver scales linearly with it:
    machine count = W*DEPTH + 2, sequence placements = one per machine, patterns = one per
    machine. So colEv / tick / patPos should each trace a straight line in W -- the same
    "vary one axis, read the slope" discipline that made bench_depth's result robust.
  * Trivial-DSP gains (stateless, one input each), so host overhead is the visible signal.
    SAME CAVEAT as bench_depth: trivial DSP makes the host-overhead *percentage* topology-
    favourable; the robust result is the *absolute* us/buffer per unit of size, not the %.
  * CONFOUND, stated: WIDTH > AudioThreads(8) oversubscribes the workers, so the dispatch /
    readWork phase columns get noisier as size grows. That is fine here -- the three loops we
    are measuring run single-threaded on the audio thread BEFORE dispatch, so their columns
    stay clean. Do NOT read the readWork/dispatch columns off this family for a size claim.

Deterministic: no MIDI, no LFOs, no humanize. Gain Multi is stateless. SH101 retriggers one
note per bar -- a single held note would decay toward silence and risk denormal stalls in the
gain chain, which is noise in the measurement, not signal. (Identical source model to
bench_depth, so the per-machine cost is directly comparable across the two families.)

    python3 src/build_bench_host.py          # sizes 8, 16, 32, 64
    python3 src/build_bench_host.py 16       # just width 16
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

DEPTH = 3                 # constant + shallow. Read the note above before changing.
BPM, TPB = 120, 4
BAR   = TPB * 4           # 16 rows/bar (4/4)
BARS  = 16
TOTAL = BARS * BAR        # 256 rows ~= 32 s at 120 BPM

SRC_NOTE       = nv(3, 0)   # C-3, retriggered every bar
SH101_NOTE_COL = 25         # Pedal SH101: monophonic, note column 25
UNITY          = 16384

# Machine-view layout: wrap chains into a compact grid so a 64-wide song does not splay
# ~25 units across the canvas. Positions are cosmetic (they touch neither audio nor the
# measurement) but must keep every visible machine > assert_no_overlap's eps (0.05) apart.
LAYOUT_COLS = 8


def build(width):
    syn = read(ref('synthref.bmxml'))    # skeleton: Master + 4 synths + editors pe1..pe5
    gan = read(ref('gainref.bmxml'))     # Pedal Gain Multi template (saved with 4 inputs)
    chd = read(ref('chordref.bmxml'))    # Modern Pattern Editor template

    GAINMULTI_TMPL = next(b for b in machine_blocks(gan) if lib_of(b) == 'Pedal Gain Multi')
    MPE_TMPL = next(b for b in machine_blocks(chd)
                    if lib_of(b) == 'Modern Pattern Editor' and name_of(b) == '_x0001_pe3')

    PAT = pattern_xml('00', TOTAL)
    final_blocks, seqs, conns, editors = [], [], [], []

    # Keep ONLY the SH101 source and drop Lead/Pad/Comp -- a benchmark wants one
    # deterministic source, not a band. The skeleton name 'Bass' is kept deliberately:
    # renaming a skeleton block is a mutation we don't need. (Same as bench_depth.)
    SRC, SRC_EDITOR = 'Bass', '_x0001_pe2'

    for b in machine_blocks(syn):
        lib, nm = lib_of(b), name_of(b)
        if lib == 'Master':
            mb = b.replace('<Patterns />', PAT, 1)
            # Master is <Type>Master</Type> -- host-positioned, stays at (0,0). set_position
            # only moves Generator/Effect blocks, so we lay the grid clear of the origin below.
            final_blocks.append(mb)
            seqs.append(('Master', [(0, TOTAL, '00')]))
        elif nm == '_x0001_pe1':                              # Master's editor = tempo
            final_blocks.append(set_data(b, build_blob_cols(
                'Master', '00', 3, {1: [(0, BPM)], 2: [(0, TPB)]})))
            editors.append('_x0001_pe1')
        elif lib == 'Pedal SH101':
            sb = set_position(set_track_count(set_patterns(b, PAT), 1), 0.0, -0.60)
            final_blocks.append(sb)
            seqs.append((SRC, [(0, TOTAL, '00')]))
        elif nm == SRC_EDITOR:                                # one note-on per bar
            ev = {(0, SH101_NOTE_COL): [(bar * BAR, SRC_NOTE) for bar in range(BARS)]}
            final_blocks.append(set_data(b, build_blob_mt(
                SRC, '00', [SH101_NOTE_COL], 1, ev)))
            editors.append(SRC_EDITOR)
        # Lead / Pad / Comp and editors pe3..pe5 are deliberately dropped.

    ed_n = 10                                   # gain editors start clear of pe1..pe5
    grid = [[None] * DEPTH for _ in range(width)]

    for chain in range(width):
        col = chain % LAYOUT_COLS
        row_block = chain // LAYOUT_COLS
        for level in range(DEPTH):
            gname = 'G%d_%02d' % (chain, level)
            ename = '_x0001_pe%d' % ed_n
            ed_n += 1

            gb = set_name(GAINMULTI_TMPL, 'PGainMul', gname)
            gb = set_patterns(set_editor(gb, ename), PAT)
            # MANDATORY: gainref's template is saved with 4 input channels; our chain gains
            # take exactly ONE input. The Input group's TrackCount must equal the connection
            # count or the per-input fader array is wrong. (Same requirement as bench_depth.)
            gb = set_input_tracks(gb, 1)
            gb = set_param(gb, 'Amp', UNITY)
            # wrapped grid: each (chain,level) is a unique compact cell, all >0.05 apart
            gx = -1.40 + col * 0.36
            gy = 0.60 + row_block * (DEPTH * 0.30 + 0.40) + level * 0.30
            gb = set_position(gb, gx, gy)

            final_blocks.append(gb)
            final_blocks.append(set_data(set_name(MPE_TMPL, '_x0001_pe3', ename),
                                         build_blob_cols(gname, '00', 8, {})))
            seqs.append((gname, [(0, TOTAL, '00')]))
            editors.append(ename)
            grid[chain][level] = gname

    for chain in range(width):
        conns.append((SRC, grid[chain][0], UNITY, UNITY, 0, 0))          # source -> head
        for level in range(DEPTH - 1):
            conns.append((grid[chain][level], grid[chain][level+1], UNITY, UNITY, 0, 0))
        conns.append(grid[chain][DEPTH - 1])                             # tail -> Master
    conns.extend(editors)                                                # editors -> Master

    out = splice(syn, machines_xml(final_blocks),
                 connections_xml_multi(conns), sequences_xml_multi(seqs))
    out = set_loop_song_end(out, TOTAL)
    out = set_tempo(out, BPM, TPB)
    out = rename_song(out, 'synthref', 'bench_host_%02d' % width)
    out = clear_held_notes(out)
    assert_no_overlap(out)
    assert_valid(out)

    path = os.path.join(OUTDIR, 'bench_host_%02d.bmxml' % width)
    write_bmxml(path, out)
    machines = 2 + 2 + 2 * width * DEPTH          # master+ed, src+ed, (gain+ed) per cell
    placements = 1 + 1 + width * DEPTH            # master, src, one per gain (colEv driver)
    patterns = placements                         # one '00' pattern per sequenced machine
    print('WROTE %s' % path)
    print('   width=%d depth=%d  gains=%d  audio connections=%d  machines=%d'
          % (width, DEPTH, width * DEPTH, width * DEPTH + width, machines))
    print('   host-loop drivers: sequencedMachines(tick)=%d  placements(colEv)=%d  patterns(patPos)=%d'
          % (placements, placements, patterns))
    print('   EXPECT on the wave path: barriersPerBuffer == %.2f (constant across sizes)' % DEPTH)
    return path


if __name__ == '__main__':
    for w in [int(a) for a in sys.argv[1:]] or [8, 16, 32, 64]:
        build(w)
