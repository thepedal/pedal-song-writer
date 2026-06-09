#!/usr/bin/env python3
"""Build "Limani" — D-Hijaz, 60 BPM, ~64 s, 28 machines.

A worked example of the rebuzz package: a 4-piece Pedal Plaits drum kit played
directly, four synths each driven by its own Pedal Chord control machine, and a
Pedal Presetter setting timbres. All format-level mechanics live in `rebuzz`;
this script only declares the music, the arrangement, and the machine wiring.
"""
import os
from rebuzz import (
    NOTE_OFF, note_value as nv,
    build_blob, build_blob_mt, build_blob_cols,
    read, machine_blocks, name_of, lib_of,
    pattern_xml, set_patterns, set_data, set_track_count, set_position,
    set_name, set_editor, assert_no_overlap, assert_valid,
    pedal_chord_state, pedal_chord_pattern,
    presetter_state, presetter_clear_stored_presets,
    machines_xml, connections_xml, sequences_xml,
    splice, set_loop_song_end, set_tempo, rename_song, clear_held_notes,
    write_bmxml,
)

# --- paths: resolve refs relative to the repo, overridable by env vars -------
_HERE = os.path.dirname(os.path.abspath(__file__))
REFS  = os.environ.get("REBUZZ_REFS") or os.path.join(_HERE, "..", "refs")
OUT   = os.environ.get("REBUZZ_OUT")  or os.path.join(_HERE, "..", "songs", "Limani.bmxml")
def ref(name): return os.path.join(REFS, name)

# --- load reference songs and the templates we splice from -------------------
syn = read(ref('synthref.bmxml'))            # skeleton + 4 synth blocks
drm = read(ref('DrumTest.bmxml'))            # 4 Pedal Plaits drums
chd = read(ref('chordref.bmxml'))            # Pedal Chord + pattern-editor template
pre = read(ref('presetter_ref.bmxml'))       # Pedal Presetter template

PRESETTER_TMPL = next(b for b in machine_blocks(pre) if lib_of(b) == 'Pedal Presetter')
PDLCHRD_TMPL = next(b for b in machine_blocks(chd) if lib_of(b) == 'Pedal Chord')
MPE_TMPL = next(b for b in machine_blocks(chd)
                if lib_of(b) == 'Modern Pattern Editor' and name_of(b) == '_x0001_pe3')
sblocks = machine_blocks(syn)
dblocks = machine_blocks(drm)

# --- song constants ----------------------------------------------------------
BPM, TPB = 60, 4
BAR = 16                       # rows per bar (TPB 4, 4/4)
BARS = 16
TOTAL = BARS * BAR             # 256 rows
def bar(b, r): return b * BAR + r
PAT = pattern_xml('00', TOTAL)

# D Hijaz: D Eb F# G A Bb C
D, Eb, Fs, G, A, Bb, C = 2, 3, 6, 7, 9, 10, 0
roots = [D, D, Eb, D, G, G, A, D, D, Eb, Bb, A, G, Eb, A, D]   # per-bar root degree

# ============================ MUSICAL CONTENT ================================
# Bass (SH101 oct2): root on rows 0 & 8 every bar
bass = []
for b in range(16):
    bass += [(bar(b, 0), nv(2, roots[b])), (bar(b, 8), nv(2, roots[b]))]
# Pad (invFFT oct4): root on row 0 each bar
pad = [(bar(b, 0), nv(4, roots[b])) for b in range(16)]
# Comp (Juno106 oct3): rows 4 & 12 from bar 9
comp = []
for b in range(8, 16):
    comp += [(bar(b, 4), nv(3, roots[b])), (bar(b, 12), nv(3, roots[b]))]
# Lead (Faze-R oct4/5): composed phrase, bars 5-16
lead_spec = {
    4:  [(0, 4, A), (4, 4, Bb), (8, 4, A), (12, 4, G)],
    5:  [(0, 4, Fs), (6, 4, G), (12, 4, A)],
    6:  [(0, 4, Bb), (4, 4, A), (8, 4, G), (12, 4, Fs)],
    7:  [(0, 4, G), (8, 4, Fs), (12, 4, Eb)],
    8:  [(0, 5, D), (6, 5, C), (12, 4, Bb)],
    9:  [(0, 4, A), (8, 4, Bb)],
    10: [(0, 5, C), (4, 4, Bb), (8, 4, A), (12, 4, G)],
    11: [(0, 4, A), (8, 4, G)],
    12: [(0, 4, G), (4, 4, Fs), (8, 4, G), (12, 4, A)],
    13: [(0, 4, Eb), (8, 4, Fs)],
    14: [(0, 4, G), (4, 4, A), (8, 4, Bb), (12, 4, A)],
    15: [(0, 4, D)],
}
lead = []
for b, notes in lead_spec.items():
    for (r, octv, idx) in notes:
        lead.append((bar(b, r), nv(octv, idx)))
# Drums (Plaits, trigger value 65 = C-4)
HIT = 65
kick = []
for b in range(2, 16):
    kick += [(bar(b, 0), HIT), (bar(b, 8), HIT)]
snare = []
for b in range(4, 16):
    snare += [(bar(b, 4), HIT), (bar(b, 12), HIT)]
hatc = []
for b in range(2, 16):
    for r in (0, 2, 4, 6, 8, 10, 12, 14):
        hatc.append((bar(b, r), HIT))
hato = []
for b in range(2, 16):
    hato.append((bar(b, 14), HIT))

# ========================= MACHINE CONFIGURATION =============================
# Per-synth track config. SH101 (Bass) is monophonic — 1 track. Others get 6
# (chord targets need >=3 tracks). Melody lives in track 0.
SYNTH_CFG = {
    'Bass': dict(tracks=1, tcols=[25],     notecol=25, events=bass),
    'Comp': dict(tracks=6, tcols=[25],     notecol=25, events=comp),
    'Pad':  dict(tracks=6, tcols=[28],     notecol=28, events=pad),
    'Lead': dict(tracks=6, tcols=[67, 68], notecol=67, events=lead),
}
# drums use the simple single-track builder: (ncols, notecol, events)
DRUM_PARTS = {
    'Kick': (14, 12, kick), 'Snare': (14, 12, snare),
    'HatClosed': (14, 12, hatc), 'HatOpen': (14, 12, hato),
}
LIB2SYNTH = {'Pedal SH101': 'Bass', 'Pedal Faze-R': 'Lead',
             'Pedal invFFT': 'Pad', 'Pedal Juno106': 'Comp'}
ED2GEN = {'_x0001_pe2': 'Bass', '_x0001_pe3': 'Lead',
          '_x0001_pe4': 'Pad', '_x0001_pe5': 'Comp'}
# distinct machine-view positions (synths keep synthref's; only drums need placing)
DRUM_POS = {'Kick': (-1.2, 0.4), 'Snare': (-0.6, 0.4),
            'HatClosed': (-1.2, 1.0), 'HatOpen': (-0.6, 1.0)}

# Loop-safety rule (see build_lastcall.py): held-note synths that get no note-on at
# song tick 0 must emit a note-off on every track at row 0, so they don't drone when
# the song loops. Computed from each synth's row-0 content. Pad/Bass open on row 0.
TRIGGERS_AT_0 = {gen for gen, c in SYNTH_CFG.items()
                 if any(r == 0 and v != NOTE_OFF for r, v in c['events'])}

# ============================== ASSEMBLY =====================================
final_blocks = []

# ---- synthref blocks: Master + tempo editor + the 4 synths (patterns emptied,
#      because each synth's notes are injected live by its Pedal Chord) ----
for b in sblocks:
    lib, nm = lib_of(b), name_of(b)
    if lib == 'Master':
        final_blocks.append(b.replace('<Patterns />', PAT, 1))          # Master gets a '00' pattern
    elif nm == '_x0001_pe1':
        mblob = build_blob_cols('Master', '00', 3, {1: [(0, BPM)], 2: [(0, TPB)]})
        final_blocks.append(set_data(b, mblob))                          # Master editor: tempo pattern
    elif lib in LIB2SYNTH:
        gen = LIB2SYNTH[lib]
        final_blocks.append(set_track_count(set_patterns(b, PAT), SYNTH_CFG[gen]['tracks']))
    elif nm in ED2GEN:
        gen = ED2GEN[nm]; c = SYNTH_CFG[gen]
        ev = {} if gen in TRIGGERS_AT_0 else \
             {(t, c['notecol']): [(0, NOTE_OFF)] for t in range(c['tracks'])}
        final_blocks.append(set_data(b, build_blob_mt(gen, '00', c['tcols'], c['tracks'], ev)))
    else:
        final_blocks.append(b)

# ---- drum blocks from DrumTest (renumber editors pe2..pe5 -> pe6..pe9) ----
drum_gen = {name_of(b): b for b in dblocks if lib_of(b) == 'Pedal Plaits'}
drum_ed = {name_of(b): b for b in dblocks if name_of(b) in ('_x0001_pe2', '_x0001_pe3', '_x0001_pe4', '_x0001_pe5')}
DRUM_ORDER = [('Kick', '_x0001_pe2', '_x0001_pe6'), ('Snare', '_x0001_pe3', '_x0001_pe7'),
              ('HatClosed', '_x0001_pe4', '_x0001_pe8'), ('HatOpen', '_x0001_pe5', '_x0001_pe9')]
for gen, oldpe, newpe in DRUM_ORDER:
    gb = set_editor(drum_gen[gen], newpe)
    gb = set_patterns(gb, PAT)
    gb = set_position(gb, *DRUM_POS[gen])
    final_blocks.append(gb)
    ncols, notecol, evs = DRUM_PARTS[gen]
    eb = set_name(drum_ed[oldpe], oldpe, newpe)
    eb = set_data(eb, build_blob(gen, [dict(name='00', ncols=ncols, notecol=notecol, events=evs)]))
    final_blocks.append(eb)

# ---- Pedal Chord control layer ----------------------------------------------
# Each Pedal Chord (Type Generator, no audio connection) drives one synth. It
# reads root (col 0) + chord type (col 2) + arp params; the machine builds the
# chord/arp internally. Chord index per D-Hijaz degree.
def chord_idx(noteidx):
    return {2: 0, 3: 0, 7: 1, 9: 5, 10: 6}[noteidx]   # D/Eb Maj, G Min, A dim, Bb aug

R = [2, 2, 3, 2, 7, 7, 9, 2, 2, 3, 10, 9, 7, 3, 9, 2]   # per-bar roots (noteIdx)
def col_roots(octv, bars, rows):
    return [(b * 16 + r, nv(octv, R[b])) for b in bars for r in rows]
def col_types(bars, rows):
    return [(b * 16 + r, chord_idx(R[b])) for b in bars for r in rows]

# (pcname, target, editor, position, colevents). Positions form a 2x2 cluster
# inside the populated canvas region (visible machines span X[-1.2,0.82] Y[-1.25,1.0]).
PEDAL_CHORDS = [
    ('PadChord', 'Pad', '_x0001_pe12', (-0.35, 0.95),     # block chords, all bars, bar-start, oct4
        {0: col_roots(4, range(16), [0]), 2: col_types(range(16), [0])}),
    ('CompChord', 'Comp', '_x0001_pe13', (0.05, 0.95),    # block stabs, bars 9-16, rows 4&12, oct3
        {0: col_roots(3, range(8, 16), [4, 12]), 2: col_types(range(8, 16), [4, 12])}),
    ('LeadArp', 'Lead', '_x0001_pe11', (0.05, 0.60),      # arp Up, bars 5-16, oct4
        {0: col_roots(4, range(4, 16), [0]), 2: col_types(range(4, 16), [0]),
         3: [(0, 1)], 4: [(0, 2)], 6: [(0, 2)], 13: [(0, 1)]}),
    ('BassArp', 'Bass', '_x0001_pe10', (-0.35, 0.60),     # arp Up octave-bass, all bars, oct2
        {0: col_roots(2, range(16), [0]), 2: [(b * 16, 50) for b in range(16)],
         3: [(0, 1)], 4: [(0, 8)], 6: [(0, 1)], 13: [(0, 1)]}),
]
for pcname, target, ped, pos, colevents in PEDAL_CHORDS:
    # Enter on the timeline, not at the start: a Pedal Chord with no root at row 0
    # gets a note-off (255) there, so it stays silent until its first real root
    # instead of sounding a stale/looped root at tick 0 (BMXML §12.9).
    col0 = colevents.get(0, [])
    if not any(r == 0 for r, _ in col0):
        colevents = {**colevents, 0: [(0, NOTE_OFF)] + list(col0)}
    gb = set_name(PDLCHRD_TMPL, 'PdlChrd', pcname)
    gb = set_editor(gb, ped)
    gb = set_patterns(gb, PAT)
    gb = set_data(gb, pedal_chord_state(target, 0))       # retarget
    gb = set_position(gb, *pos)
    final_blocks.append(gb)
    eb = set_name(MPE_TMPL, '_x0001_pe3', ped)
    eb = set_data(eb, pedal_chord_pattern(pcname, colevents))
    final_blocks.append(eb)

# ---- Pedal Presetter (preset automation) ------------------------------------
# One multi-track control machine: each track -> one synth, firing a preset index
# (0-based bank position). Stagger one fire per row (rows 0,1,2): firing all on
# one row hits the Build-1827 same-row parametersChanged collision (BMXML §12.10).
PRESETS = [('Pad', 46),    # invFFT "Pad - Soft Strings" (audible from bar 1 -> fire first)
           ('Lead', 58),   # Faze-R "Pluck - Reso Tine"
           ('Comp', 17)]   # Juno106 "Classic - Polysynth"
ps_targets = [t for t, _ in PRESETS]
ps_events = {(i, 0): [(i, idx)] for i, (_, idx) in enumerate(PRESETS)}   # Preset col 0, staggered rows
ps_blob = build_blob_mt('Presets', '00', [0], len(PRESETS), ps_events)

pb = set_name(PRESETTER_TMPL, 'Presetter', 'Presets')
pb = set_editor(pb, '_x0001_pe14')
pb = set_patterns(pb, PAT)
pb = set_data(pb, presetter_state(ps_targets))
pb = set_track_count(pb, len(PRESETS))
pb = presetter_clear_stored_presets(pb, len(PRESETS))     # no load-time fire
pb = set_position(pb, 0.4, 0.7)
final_blocks.append(pb)
final_blocks.append(set_data(set_name(MPE_TMPL, '_x0001_pe3', '_x0001_pe14'), ps_blob))

# ---- wiring: connections (editors + audio gens -> Master; control gens none),
#      sequences (every generator + Master + each control machine) ----
conn_sources = ['_x0001_pe1',
                '_x0001_pe2', 'Bass', '_x0001_pe3', 'Lead', '_x0001_pe4', 'Pad', '_x0001_pe5', 'Comp',
                'Kick', '_x0001_pe6', 'Snare', '_x0001_pe7', 'HatClosed', '_x0001_pe8', 'HatOpen', '_x0001_pe9',
                '_x0001_pe10', '_x0001_pe11', '_x0001_pe12', '_x0001_pe13',   # Pedal Chord editors
                '_x0001_pe14']                                                 # Presetter editor
seq_machines = ['Master', 'Kick', 'Snare', 'HatClosed', 'HatOpen', 'Bass', 'Lead', 'Pad', 'Comp',
                'PadChord', 'CompChord', 'LeadArp', 'BassArp', 'Presets']

# ---- splice into the synthref skeleton and finish ---------------------------
out = splice(syn, machines_xml(final_blocks), connections_xml(conn_sources),
             sequences_xml(seq_machines, TOTAL))
out = set_loop_song_end(out, TOTAL)
out = set_tempo(out, BPM, TPB)
out = rename_song(out, 'synthref', 'Limani')
out = clear_held_notes(out)

out = assert_no_overlap(out)                    # no two visible machines may stack
out = assert_valid(out)                         # full structural + loop-safety validation
n = write_bmxml(OUT, out)
print('WROTE %s bytes=%d' % (OUT, n))
