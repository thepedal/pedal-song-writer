#!/usr/bin/env python3
"""Build a 'machine reference' .bmxml seeded with one clean instance of every
managed machine the song-writer currently holds a verified block for. It loads
and validates, so it opens in ReBuzz as a starting point: drag in the machines
listed in the accompanying checklist, re-save, and it becomes the canonical
all-machines reference to feed back for characterisation.

Only machines we already have are placed here -- nothing is fabricated.
"""
import os
from rebuzz import (read, machine_blocks, name_of, lib_of, pattern_xml,
                    set_patterns, set_data, set_track_count, set_position, set_name, set_editor,
                    build_blob, build_blob_mt, build_blob_cols,
                    pedal_chord_state, presetter_state,
                    machines_xml, connections_xml_multi, sequences_xml_multi,
                    splice, set_tempo, set_loop_song_end, rename_song, clear_held_notes,
                    write_bmxml, assert_valid)

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.environ.get('REBUZZ_REFS') or os.path.join(HERE, '..', 'refs')
def ref(n): return read(os.path.join(REFS, n))
syn, drm, chd = ref('synthref.bmxml'), ref('DrumTest.bmxml'), ref('chordref.bmxml')
pre, gan, lmt = ref('presetter_ref.bmxml'), ref('gainref.bmxml'), ref('limitref.bmxml')

def tmpl(xml, libname):
    return next(b for b in machine_blocks(xml) if lib_of(b) == libname)

MPE  = tmpl(chd, 'Modern Pattern Editor')
TOTAL, PAT = 64, pattern_xml('00', 64)
blocks, conns, seqs = [], [], []
pe = [1]                                                   # pe1 is Master's editor
def next_pe():
    pe[0] += 1; return '_x0001_pe%d' % pe[0]

# Master + its editor (from synthref)
for b in machine_blocks(syn):
    if lib_of(b) == 'Master':
        blocks.append(b.replace('<Patterns />', PAT, 1)); seqs.append(('Master', [(0, TOTAL, '00')]))
    elif name_of(b) == '_x0001_pe1':
        blocks.append(set_data(b, build_blob_cols('Master', '00', 3, {}))); conns.append('_x0001_pe1')

# (name, source-xml, library, kind, editor-blob-factory)
GEN = lambda nm, cols, trks: (lambda: build_blob_mt(nm, '00', cols, trks, {}))
spec = [
    ('Plaits',   drm, 'Pedal Plaits',     'gen',  lambda: build_blob('Plaits', [dict(name='00', ncols=14, notecol=12, events=[])])),
    ('SH101',    syn, 'Pedal SH101',      'gen',  GEN('SH101',   [25],     1)),
    ('Faze-R',   syn, 'Pedal Faze-R',     'gen',  GEN('Faze-R',  [67, 68], 1)),
    ('invFFT',   syn, 'Pedal invFFT',     'gen',  lambda: build_blob_mt('invFFT', '00', [28], 1, {(0, 28): [(0, 255)]})),
    ('Juno106',  syn, 'Pedal Juno106',    'gen',  GEN('Juno106', [25],     1)),
    ('PChord',   chd, 'Pedal Chord',      'ctrl', lambda: build_blob_cols('PChord', '00', 14, {})),
    ('Presetter', pre, 'Pedal Presetter', 'ctrl', lambda: build_blob_mt('Presetter', '00', [0], 1, {})),
    ('GainMulti', gan, 'Pedal Gain Multi', 'fx',  lambda: build_blob_cols('GainMulti', '00', 8, {})),
    ('Limit',    lmt, 'Pedal Limit',      'fx',   lambda: build_blob_cols('Limit', '00', 3, {})),
]
# tidy grid layout (visible machines only); Master sits at slot 0
POS = [(-1.0, -0.8), (-0.4, -0.8), (0.2, -0.8), (0.7, -0.8),
       (-1.0, -0.2), (-0.4, -0.2), (0.2, -0.2), (0.7, -0.2),
       (-1.0, 0.4), (-0.4, 0.4)]
blocks[0] = set_position(blocks[0], *POS[0])               # Master

for i, (nm, src, lib, kind, blobf) in enumerate(spec):
    mb = tmpl(src, lib)
    ed = next_pe()
    mb = set_editor(set_name(mb, name_of(mb), nm), ed)
    mb = set_patterns(mb, PAT)
    if kind == 'gen':
        mb = set_track_count(mb, 1)
    elif lib == 'Pedal Chord':
        mb = set_data(mb, pedal_chord_state('invFFT', 0))  # target an existing generator
    elif lib == 'Pedal Presetter':
        mb = set_track_count(set_data(mb, presetter_state(['invFFT'])), 1)
    mb = set_position(mb, *POS[i + 1])
    blocks.append(mb)
    blocks.append(set_data(set_name(MPE, name_of(MPE), ed), blobf()))
    conns.append(ed)                                       # editor -> Master
    if kind in ('gen', 'fx'):
        conns.append(nm)                                   # audio out -> Master
    seqs.append((nm, [(0, TOTAL, '00')]))

out = splice(syn, machines_xml(blocks), connections_xml_multi(conns), sequences_xml_multi(seqs))
out = rename_song(set_tempo(set_loop_song_end(out, TOTAL), 120, 4), 'synthref', 'MachineRef')
out = clear_held_notes(out)
out = assert_valid(out)
OUT = os.path.join(HERE, '..', 'songs', 'MachineRef.bmxml')
print('WROTE %s bytes=%d  (%d machines placed)' % (OUT, write_bmxml(OUT, out), len(spec) + 1))
