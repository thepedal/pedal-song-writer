#!/usr/bin/env python3
"""Build "Last Call" — swung A-blues, 90 BPM, 8 TPB, ~2:08.

Same 28-machine rig and same music as the flat version, but the drums and the
four Pedal Chords now carry one named pattern per SECTION (Intro / Verse /
Chorus / Mid8 / Outro), placed on the timeline by the sequencer — so the song is
navigable as a human arrangement. The Verse and Chorus patterns are authored
once and reused at both occurrences. Synths (empty, control-driven), Master
(tempo) and Presetter stay single-pattern.
"""
import os
from rebuzz import (
    NOTE_OFF, note_value as nv,
    build_blob, build_blob_mt, build_blob_cols, build_blob_cols_multi,
    read, machine_blocks, name_of, lib_of,
    pattern_xml, patterns_xml, set_patterns, set_data, set_track_count, set_position,
    set_name, set_editor, set_param, set_param_track, assert_no_overlap, assert_valid,
    pedal_chord_state, pedal_chord_pattern,
    presetter_state, presetter_clear_stored_presets,
    machines_xml, connections_xml_multi, sequences_xml_multi,
    splice, set_loop_song_end, set_tempo, rename_song, clear_held_notes, write_bmxml,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
REFS  = os.environ.get("REBUZZ_REFS") or os.path.join(_HERE, "..", "refs")
OUT   = os.environ.get("REBUZZ_OUT")  or os.path.join(_HERE, "..", "songs", "LastCall.bmxml")
def ref(name): return os.path.join(REFS, name)
syn = read(ref('synthref.bmxml')); drm = read(ref('DrumTest.bmxml'))
chd = read(ref('chordref.bmxml')); pre = read(ref('presetter_ref.bmxml'))
gan = read(ref('gainref.bmxml'))
PRESETTER_TMPL = next(b for b in machine_blocks(pre) if lib_of(b) == 'Pedal Presetter')
PDLCHRD_TMPL = next(b for b in machine_blocks(chd) if lib_of(b) == 'Pedal Chord')
GAINMULTI_TMPL = next(b for b in machine_blocks(gan) if lib_of(b) == 'Pedal Gain Multi')
MPE_TMPL = next(b for b in machine_blocks(chd)
                if lib_of(b) == 'Modern Pattern Editor' and name_of(b) == '_x0001_pe3')
sblocks = machine_blocks(syn); dblocks = machine_blocks(drm)

# --- constants & form --------------------------------------------------------
BPM, TPB = 90, 8
BAR = TPB * 4                                  # 32 rows/bar
A, D, E, B = 9, 2, 4, 11
SEC_ROOTS = {'Intro': [A, A, D, E],
             'Verse': [A, A, D, D, A, E, A, E],
             'Chorus': [D, D, A, A, E, D, A, E],
             'Mid8': [D, D, A, A, B, B, E, E],
             'Outro': [A, D, A, A]}
SEC_BARS = {k: len(v) for k, v in SEC_ROOTS.items()}
ARRANGE = [('Intro', 0), ('Verse', 4), ('Chorus', 12), ('Verse', 20),
           ('Mid8', 28), ('Chorus', 36), ('Outro', 44)]    # (section, start-bar)
TOTAL = (ARRANGE[-1][1] + SEC_BARS[ARRANGE[-1][0]]) * BAR   # 48 bars -> 1536 rows
UNIQUE = []
for nm, _ in ARRANGE:
    if nm not in UNIQUE: UNIQUE.append(nm)                  # Intro,Verse,Chorus,Mid8,Outro
def sec_len_rows(nm): return SEC_BARS[nm] * BAR
PAT = pattern_xml('00', TOTAL)                              # single whole-song pattern

# --- per-section content (RELATIVE rows within the section) ------------------
# Pedal Chords -> colevents dict, or None if the machine doesn't play the section.
def pad_cc(nm, r):    # block chords, oct 4, every bar
    return {0: [(b * BAR, nv(4, r[b])) for b in range(len(r))],
            2: [(b * BAR, 2) for b in range(len(r))]}
BASS_CFG = {3: [(0, 1)], 4: [(0, 8)], 6: [(0, 1)], 13: [(0, 1)]}   # Up, Speed 8, Oct 1
def bass_cc(nm, r):   # boogie arp, oct 2, every bar
    ce = {0: [(b * BAR, nv(2, r[b])) for b in range(len(r))],
          2: [(b * BAR, 2) for b in range(len(r))]}; ce.update(BASS_CFG); return ce
COMP_ROWS = {'Verse': [8, 24], 'Chorus': [0, 8, 16, 24], 'Mid8': [0], 'Outro': [0]}
def comp_cc(nm, r):   # EP block stabs, oct 3
    if nm not in COMP_ROWS: return None
    rows = COMP_ROWS[nm]
    return {0: [(b * BAR + x, nv(3, r[b])) for b in range(len(r)) for x in rows],
            2: [(b * BAR + x, 2) for b in range(len(r)) for x in rows]}
LEAD_CFG = {3: [(0, 3)], 4: [(0, 4)], 6: [(0, 2)], 9: [(0, 50)], 10: [(0, 1)], 13: [(0, 1)]}
def lead_cc(nm, r):   # swung Up+Down arp, oct 5; choruses + bridge only
    if nm not in ('Chorus', 'Mid8'): return None
    ce = {0: [(b * BAR, nv(5, r[b])) for b in range(len(r))],
          2: [(b * BAR, 2) for b in range(len(r))]}; ce.update(LEAD_CFG); return ce

# Drums -> relative (row, value) lists, or None. notecol 12, trigger 65.
HIT = 65
HATC_ROWS = [0, 5, 8, 13, 16, 21, 24, 29]      # swung eighths
HIGH = {'Chorus', 'Mid8'}
def hatc_d(nm):
    play = [2, 3] if nm == 'Intro' else range(SEC_BARS[nm])   # intro: only bars 2-3
    return [(b * BAR + x, HIT) for b in play for x in HATC_ROWS]
def kick_d(nm):
    if nm == 'Intro': return [(b * BAR + x, HIT) for b in [2, 3] for x in [0, 16]]
    rows = [0, 16] + ([11] if nm in HIGH else [])
    return [(b * BAR + x, HIT) for b in range(SEC_BARS[nm]) for x in rows]
def snare_d(nm):
    if nm == 'Intro': return None
    nb = SEC_BARS[nm]; out = []
    if nm == 'Outro':
        for b in range(nb - 1): out += [(b * BAR + 8, HIT), (b * BAR + 24, HIT)]
        lb = (nb - 1) * BAR; out += [(lb + x, HIT) for x in [0, 8, 16, 20, 24, 28, 31]]
        return out
    for b in range(nb):                                       # backbeat + section-end fill
        out += [(b * BAR + 8, HIT), (b * BAR + 24, HIT)]
        if b == nb - 1: out += [(b * BAR + 28, HIT), (b * BAR + 31, HIT)]
    return out
def hato_d(nm):
    if nm == 'Intro': return [(3 * BAR + 29, HIT)]            # one push at end of intro
    if nm in HIGH: return [(b * BAR + 29, HIT) for b in range(SEC_BARS[nm])]
    return None                                               # silent in verses/outro

# ============================ ASSEMBLY =======================================
SYNTH_CFG = {'Bass': dict(tracks=1, tcols=[25]), 'Comp': dict(tracks=6, tcols=[25]),
             'Pad': dict(tracks=6, tcols=[28]), 'Lead': dict(tracks=6, tcols=[67, 68])}
LIB2SYNTH = {'Pedal SH101': 'Bass', 'Pedal Faze-R': 'Lead', 'Pedal invFFT': 'Pad', 'Pedal Juno106': 'Comp'}
ED2GEN = {'_x0001_pe2': 'Bass', '_x0001_pe3': 'Lead', '_x0001_pe4': 'Pad', '_x0001_pe5': 'Comp'}
DRUM_POS = {'Kick': (-1.2, 0.4), 'Snare': (-0.6, 0.4), 'HatClosed': (-1.2, 1.0), 'HatOpen': (-0.6, 1.0)}

# Loop-safety rule (held-note generators): a synth that receives NO note-on at
# song tick 0 must emit a note-OFF on every one of its tracks at row 0 of its own
# whole-song pattern. Otherwise, when the song loops, nothing releases the voice it
# held from the end of the song and it drones -- its Pedal Chord's own row-0 note-off
# is no help here, because in a sectioned arrangement that chord isn't even sequenced
# at tick 0 (it enters at the verse/chorus). Pad and Bass fire a root at tick 0, so
# they re-articulate cleanly on the loop and are exempt. Drums are one-shot (Plaits)
# and can't drone, so the rule doesn't apply to them.
SYNTH_DRIVER = {'Pad': pad_cc, 'Bass': bass_cc, 'Comp': comp_cc, 'Lead': lead_cc}
_first = ARRANGE[0][0]
def _triggers_at_tick0(fn):
    ce = fn(_first, SEC_ROOTS[_first])
    return bool(ce) and any(r == 0 and v != NOTE_OFF for r, v in ce.get(0, []))
TRIGGERS_AT_0 = {g for g, fn in SYNTH_DRIVER.items() if _triggers_at_tick0(fn)}

final_blocks = []
seqs = []                                                     # (machine, placements)

# synthref: Master(tempo) + synths(empty whole-song, control-driven)
for b in sblocks:
    lib, nm = lib_of(b), name_of(b)
    if lib == 'Master':
        final_blocks.append(b.replace('<Patterns />', PAT, 1))
        seqs.append(('Master', [(0, TOTAL, '00')]))
    elif nm == '_x0001_pe1':
        final_blocks.append(set_data(b, build_blob_cols('Master', '00', 3, {1: [(0, BPM)], 2: [(0, TPB)]})))
    elif lib in LIB2SYNTH:
        gen = LIB2SYNTH[lib]
        final_blocks.append(set_track_count(set_patterns(b, PAT), SYNTH_CFG[gen]['tracks']))
        seqs.append((gen, [(0, TOTAL, '00')]))
    elif nm in ED2GEN:
        gen = ED2GEN[nm]; c = SYNTH_CFG[gen]
        ev = {} if gen in TRIGGERS_AT_0 else \
             {(t, c['tcols'][0]): [(0, NOTE_OFF)] for t in range(c['tracks'])}
        final_blocks.append(set_data(b, build_blob_mt(gen, '00', c['tcols'], c['tracks'], ev)))
    else:
        final_blocks.append(b)

# drums: per-section patterns (direct Plaits)
drum_gen = {name_of(b): b for b in dblocks if lib_of(b) == 'Pedal Plaits'}
drum_ed = {name_of(b): b for b in dblocks if name_of(b) in ED2GEN}
DRUM_ORDER = [('Kick', '_x0001_pe2', '_x0001_pe6', kick_d), ('Snare', '_x0001_pe3', '_x0001_pe7', snare_d),
              ('HatClosed', '_x0001_pe4', '_x0001_pe8', hatc_d), ('HatOpen', '_x0001_pe5', '_x0001_pe9', hato_d)]
for gen, oldpe, newpe, fn in DRUM_ORDER:
    pats, plc, blobpats = [], [], []
    for nm in UNIQUE:
        ev = fn(nm)
        if ev is None: continue
        pats.append((nm, sec_len_rows(nm)))
        blobpats.append(dict(name=nm, ncols=14, notecol=12, events=ev))
    seen = {p[0] for p in pats}
    plc = [(start * BAR, sec_len_rows(nm), nm) for nm, start in ARRANGE if nm in seen]
    gb = set_position(set_patterns(set_editor(drum_gen[gen], newpe), patterns_xml(pats)), *DRUM_POS[gen])
    final_blocks.append(gb)
    final_blocks.append(set_data(set_name(drum_ed[oldpe], oldpe, newpe), build_blob(gen, blobpats)))
    seqs.append((gen, plc))

# Pedal Chords: per-section patterns (each drives one synth)
PEDAL_CHORDS = [('PadChord', 'Pad', '_x0001_pe12', (-0.35, 0.95), pad_cc),
                ('CompChord', 'Comp', '_x0001_pe13', (0.05, 0.95), comp_cc),
                ('LeadArp', 'Lead', '_x0001_pe11', (0.05, 0.60), lead_cc),
                ('BassArp', 'Bass', '_x0001_pe10', (-0.35, 0.60), bass_cc)]
for pcname, target, ped, pos, fn in PEDAL_CHORDS:
    pats, blobpats = [], []
    for nm in UNIQUE:
        ce = fn(nm, SEC_ROOTS[nm])
        if ce is None: continue
        col0 = ce.get(0, [])
        if not any(r == 0 for r, _ in col0):          # open on a root, else note-off (§12.9)
            ce = {**ce, 0: [(0, NOTE_OFF)] + list(col0)}
        pats.append((nm, sec_len_rows(nm)))
        blobpats.append((nm, 14, ce))
    seen = {p[0] for p in pats}
    plc = [(start * BAR, sec_len_rows(nm), nm) for nm, start in ARRANGE if nm in seen]
    gb = set_position(set_data(set_patterns(set_editor(set_name(PDLCHRD_TMPL, 'PdlChrd', pcname), ped),
                      patterns_xml(pats)), pedal_chord_state(target, 0)), *pos)
    final_blocks.append(gb)
    final_blocks.append(set_data(set_name(MPE_TMPL, '_x0001_pe3', ped),
                                 build_blob_cols_multi(pcname, blobpats)))
    seqs.append((pcname, plc))

# Presetter: timbres at the start (single pattern), staggered one per row. Bass
# goes first (row 0) so the SH101 patch is loaded before its tick-0 downbeat;
# Pad's slow attack tolerates the 1-row shift to row 1.
PRESETS = [('Bass', 0), ('Pad', 41), ('Lead', 44), ('Comp', 28)]   # Bass: SH101 'Acid Bass'; Pad: invFFT 'Pad - Dark'
ps_targets = [t for t, _ in PRESETS]
ps_events = {(i, 0): [(i, idx)] for i, (_, idx) in enumerate(PRESETS)}
pb = set_position(presetter_clear_stored_presets(
        set_track_count(set_data(set_patterns(set_editor(
            set_name(PRESETTER_TMPL, 'Presetter', 'Presets'), '_x0001_pe14'), PAT),
            presetter_state(ps_targets)), len(PRESETS)), len(PRESETS)), 0.4, 0.7)
final_blocks.append(pb)
final_blocks.append(set_data(set_name(MPE_TMPL, '_x0001_pe3', '_x0001_pe14'),
                             build_blob_mt('Presets', '00', [0], len(PRESETS), ps_events)))
seqs.append(('Presets', [(0, TOTAL, '00')]))

# Submix buses: each a Pedal Gain Multi (Type Effect, multi-in). The source
# GENERATORS feed channels 0..n-1; the bus -> Master. Per-track gain lives in the
# input connection's Amp (16384 = unity) AND the machine's per-track Amp param,
# which ReBuzz keeps in sync — both neutralised to unity so the mix is unchanged,
# just bussed. Each bus gets its own empty 8-col editor pattern. (§15)
def gain_bus(name, editor, pos, inputs):
    """Splice a Pedal Gain Multi as a submix bus. `inputs` is a list where each
    entry is `'src'` (unity) or `('src', amp)` (16384 = unity); position in the
    list is the input channel. The per-input gain is written to BOTH the input
    connection's Amp and the machine's per-track Amp param (kept in sync, as
    ReBuzz stores a fader move). Appends the bus block + editor + sequence;
    returns the connection specs (inputs + bus->Master + editor->Master)."""
    chans = [(s, 16384) if isinstance(s, str) else s for s in inputs]
    gb = set_param(set_patterns(set_editor(set_name(GAINMULTI_TMPL, 'PGainMul', name),
                                            editor), PAT), 'Amp', 16384)   # all tracks unity
    for ch, (src, amp) in enumerate(chans):
        if amp != 16384:
            gb = set_param_track(gb, 'Amp', ch, amp)
    gb = set_position(gb, *pos)
    final_blocks.append(gb)
    final_blocks.append(set_data(set_name(MPE_TMPL, '_x0001_pe3', editor),
                                 build_blob_cols(name, '00', 8, {})))
    seqs.append((name, [(0, TOTAL, '00')]))
    return ([(src, name, amp, 16384, 0, ch) for ch, (src, amp) in enumerate(chans)]
            + [name, editor])                                  # bus + its editor -> Master

drum_conns  = gain_bus('DrumBus',  '_x0001_pe15', (-0.95, -0.3), ['Kick', 'Snare', 'HatClosed', 'HatOpen'])
synth_conns = gain_bus('SynthBus', '_x0001_pe16', (-0.55, -0.3),
                       ['Bass', 'Lead', ('Pad', 652), 'Comp'])   # Pad -28 dB (from stem analysis: pad source clips, ~17 dB hot)

# connections: drum + synth generators route to their bus; editors + buses -> Master.
conns = (['_x0001_pe1', '_x0001_pe2', '_x0001_pe3', '_x0001_pe4', '_x0001_pe5',
          '_x0001_pe6', '_x0001_pe7', '_x0001_pe8', '_x0001_pe9',
          '_x0001_pe10', '_x0001_pe11', '_x0001_pe12', '_x0001_pe13', '_x0001_pe14']
         + drum_conns + synth_conns)
# order sequences as Master, drums, synths, chords, Presets, bus
order = ['Master', 'Kick', 'Snare', 'HatClosed', 'HatOpen', 'Bass', 'Lead', 'Pad', 'Comp',
         'PadChord', 'CompChord', 'LeadArp', 'BassArp', 'Presets', 'DrumBus', 'SynthBus']
seqs.sort(key=lambda mp: order.index(mp[0]))

out = splice(syn, machines_xml(final_blocks), connections_xml_multi(conns), sequences_xml_multi(seqs))
out = set_loop_song_end(out, TOTAL)
out = set_tempo(out, BPM, TPB)
out = rename_song(out, 'synthref', 'LastCall')
out = clear_held_notes(out)
out = assert_no_overlap(out)                    # no two visible machines may stack
out = assert_valid(out)                         # full structural + loop-safety validation
n = write_bmxml(OUT, out)
total_pats = sum(len(pl) for _, pl in seqs)
print('WROTE %s bytes=%d  (%d rows, %d placed patterns)' % (OUT, n, TOTAL, total_pats))
