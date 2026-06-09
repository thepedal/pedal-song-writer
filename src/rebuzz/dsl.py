"""Composition DSL: author a song from musical objects (sections with roots,
chord/arp voices, drum step-strings, an arrangement, a mix) and compile to a
validated .bmxml. The compiler is a faithful generalisation of build_lastcall.py
-- it assembles the same proven rig (synthref synths driven by Pedal Chords,
Plaits drums, two Pedal Gain Multi submix buses, optional Presetter) and reuses
the byte-exact builders in rebuzz.*.

Synth slots (fixed by synthref): Bass=SH101(mono), Lead=Faze-R, Pad=invFFT,
Comp=Juno106. Drum slots (Plaits): Kick, Snare, HatClosed, HatOpen. A voice
selects a slot by name; unused slots are dropped from the file.

    from rebuzz.dsl import Song, Section, Chords, Arp, Drums
    s = Song('Demo', bpm=90, tpb=8, key='A', scale='blues')
    s.section('Verse',  ['A','A','D','E'])
    s.section('Chorus', ['D','D','A','E'])
    s.add(Arp('Bass', octave=2, chord='dom7', mode='up', speed=8, octaves=2))
    s.add(Chords('Pad', octave=4, chord='dom7'))
    s.add(Drums({'Kick':'x...x...', 'HatClosed':'x.x.x.x.'}))
    s.arrange(['Verse', 'Chorus', 'Verse'])
    s.mix(Pad=-15)
    xml = s.compile()            # validated bmxml string
"""
import os
from .theory import Scale, chord_code, arp_mode
from .blob import (note_value as nv, NOTE_OFF,
                   build_blob, build_blob_mt, build_blob_cols, build_blob_cols_multi)
from .blocks import (read, machine_blocks, name_of, lib_of, pattern_xml, patterns_xml,
                     set_patterns, set_data, set_track_count, set_position, set_name,
                     set_editor, set_param, set_param_track)
from .control import pedal_chord_state, presetter_state, presetter_clear_stored_presets
from .song import (machines_xml, connections_xml_multi, sequences_xml_multi, splice,
                   set_loop_song_end, set_tempo, rename_song, clear_held_notes, write_bmxml)
from .validate import assert_valid

HIT = 65                                              # Plaits trigger (C-4)
SYNTH_SLOTS = {'Bass': dict(tcols=[25], tracks=1, editor='_x0001_pe2'),
               'Lead': dict(tcols=[67, 68], tracks=6, editor='_x0001_pe3'),
               'Pad':  dict(tcols=[28], tracks=6, editor='_x0001_pe4'),
               'Comp': dict(tcols=[25], tracks=6, editor='_x0001_pe5')}
DRUM_SLOTS = ['Kick', 'Snare', 'HatClosed', 'HatOpen']
_SYNTH_LIBS = {'Pedal SH101', 'Pedal Faze-R', 'Pedal invFFT', 'Pedal Juno106'}
# stable machine-view positions
_SYNTH_POS = {'Bass': (-0.35, 0.60), 'Lead': (0.05, 0.60), 'Pad': (-0.35, 0.95), 'Comp': (0.05, 0.95)}
_DRUM_POS = {'Kick': (-1.2, 0.4), 'Snare': (-0.6, 0.4), 'HatClosed': (-1.2, 1.0), 'HatOpen': (-0.6, 1.0)}
_CHORD_POS = {'Bass': (-0.75, 0.60), 'Lead': (0.45, 0.60), 'Pad': (-0.75, 0.95), 'Comp': (0.45, 0.95)}


def steps_to_rows(pattern, bar_rows):
    """A step-string is one bar split into len(pattern) equal steps; any char
    other than '.' or ' ' is a hit. Returns the hit row-offsets within a bar."""
    L = len(pattern)
    if L == 0 or bar_rows % L:
        raise ValueError('step-string length %d must divide bar (%d rows)' % (L, bar_rows))
    step = bar_rows // L
    return [i * step for i, c in enumerate(pattern) if c not in '. ']


def db_to_amp(db):
    return round(16384 * 10 ** (db / 20.0))


# ---- voices -----------------------------------------------------------------

class _SynthVoice:
    is_synth = True

    def __init__(self, slot, octave, sections=None):
        if slot not in SYNTH_SLOTS:
            raise ValueError('unknown synth slot %r (have %s)' % (slot, ', '.join(SYNTH_SLOTS)))
        self.slot = slot
        self.octave = octave
        self.sections = set(sections) if sections else None

    def active(self, section):
        return self.sections is None or section in self.sections


class Chords(_SynthVoice):
    """Block chords. `rhythm` is a one-bar step-string of strike positions."""
    def __init__(self, slot, octave, chord='maj', rhythm='x', octaves=1, sections=None):
        super().__init__(slot, octave, sections)
        self.code = chord_code(chord)
        self.rhythm = rhythm
        self.octaves = octaves

    def colevents(self, section, roots, scale, bar):
        if not self.active(section):
            return None
        rows = steps_to_rows(self.rhythm, bar)
        col0, col2 = [], []
        for b, root in enumerate(roots):
            val = scale.value(root, self.octave)
            for r in rows:
                pos = b * bar + r
                col0.append((pos, val)); col2.append((pos, self.code))
        return {0: col0, 2: col2}


class Arp(_SynthVoice):
    """Arpeggiated chord: one root per bar, plus arp config at row 0."""
    def __init__(self, slot, octave, chord='maj', mode='up', speed=4, octaves=2,
                 swing=0, sections=None):
        super().__init__(slot, octave, sections)
        self.code = chord_code(chord)
        self.mode = arp_mode(mode)
        self.speed, self.octaves, self.swing = speed, octaves, swing

    def colevents(self, section, roots, scale, bar):
        if not self.active(section):
            return None
        col0, col2 = [], []
        for b, root in enumerate(roots):
            pos = b * bar
            col0.append((pos, scale.value(root, self.octave))); col2.append((pos, self.code))
        ce = {0: col0, 2: col2, 3: [(0, self.mode)], 4: [(0, self.speed)],
              6: [(0, self.octaves)], 13: [(0, 1)]}
        if self.swing:
            ce[9] = [(0, self.swing)]; ce[10] = [(0, 1)]
        return ce


class Drums:
    is_synth = False

    def __init__(self, patterns):
        """`patterns` = {drum_slot: step-string | {section: step-string}}."""
        bad = set(patterns) - set(DRUM_SLOTS)
        if bad:
            raise ValueError('unknown drum slot(s) %s (have %s)' % (bad, ', '.join(DRUM_SLOTS)))
        self.patterns = patterns

    def rows(self, slot, section, bars, bar):
        spec = self.patterns.get(slot)
        if spec is None:
            return None
        s = spec.get(section) if isinstance(spec, dict) else spec
        if not s:
            return None
        base = steps_to_rows(s, bar)
        return [(b * bar + r, HIT) for b in range(bars) for r in base]


# ---- section + song ---------------------------------------------------------

class Section:
    def __init__(self, name, roots, bars=None):
        self.name = name
        self.roots = list(roots)
        self.bars = bars or len(self.roots)


class Song:
    def __init__(self, name, bpm, tpb=8, key='C', scale='major', refs=None):
        self.name, self.bpm, self.tpb = name, bpm, tpb
        self.scale = Scale(key, scale)
        self.bar = tpb * 4
        self._sections, self._voices, self._arrange = {}, [], []
        self._mix, self._presets = {}, {}
        self.refs = refs

    def section(self, name, roots, bars=None):
        self._sections[name] = Section(name, roots, bars)
        return self

    def add(self, voice):
        self._voices.append(voice)
        return self

    def arrange(self, section_names):
        self._arrange = list(section_names)
        return self

    def mix(self, **db):
        self._mix.update(db)
        return self

    def presets(self, **slot_to_index):
        self._presets.update(slot_to_index)
        return self

    # -- compile -------------------------------------------------------------
    def compile(self):
        return _Compiler(self).run()

    def write(self, path):
        n = write_bmxml(path, self.compile())
        return n


class _Compiler:
    def __init__(self, song):
        self.s = song
        self.bar = song.bar
        here = os.path.dirname(os.path.abspath(__file__))
        refs = song.refs or os.environ.get('REBUZZ_REFS') or os.path.join(here, '..', '..', 'refs')
        self.syn = read(os.path.join(refs, 'synthref.bmxml'))
        self.drm = read(os.path.join(refs, 'DrumTest.bmxml'))
        chd = read(os.path.join(refs, 'chordref.bmxml'))
        pre = read(os.path.join(refs, 'presetter_ref.bmxml'))
        gan = read(os.path.join(refs, 'gainref.bmxml'))
        self.PDLCHRD = next(b for b in machine_blocks(chd) if lib_of(b) == 'Pedal Chord')
        self.MPE = next(b for b in machine_blocks(chd)
                        if lib_of(b) == 'Modern Pattern Editor' and name_of(b) == '_x0001_pe3')
        self.GAIN = next(b for b in machine_blocks(gan) if lib_of(b) == 'Pedal Gain Multi')
        self.PRESETTER = next(b for b in machine_blocks(pre) if lib_of(b) == 'Pedal Presetter')
        self._pe = 6                                   # next free editor id (1-5 are synthref)
        self.blocks, self.seqs, self.editors = [], [], []

    def pe(self):
        n, self._pe = '_x0001_pe%d' % self._pe, self._pe + 1
        return n

    # arrangement maths
    def _layout(self):
        s = self.s
        if not s._arrange:
            s._arrange = list(s._sections)
        order = []
        for nm in s._arrange:
            if nm not in s._sections:
                raise ValueError('arranged section %r is not defined' % nm)
            if nm not in order:
                order.append(nm)
        arrange, start = [], 0
        for nm in s._arrange:
            arrange.append((nm, start)); start += s._sections[nm].bars
        return order, arrange, start * self.bar

    def run(self):
        s = self.s
        bar = self.bar
        order, arrange, total = self._layout()
        sec_bars = {nm: s._sections[nm].bars for nm in order}
        PAT = pattern_xml('00', total)
        synth_voices = [v for v in s._voices if getattr(v, 'is_synth', False)]
        drum_voices = [v for v in s._voices if isinstance(v, Drums)]
        used_synths = {v.slot for v in synth_voices}
        if len(used_synths) != len(synth_voices):
            raise ValueError('each synth slot may host only one voice')

        # which synth voices fire a root at song tick 0 (first arranged section)?
        first = arrange[0][0]

        def fires_at_0(v):
            ce = v.colevents(first, s._sections[first].roots, s.scale, bar)
            return bool(ce) and any(r == 0 and val != NOTE_OFF for r, val in ce.get(0, []))
        triggers0 = {v.slot for v in synth_voices if fires_at_0(v)}

        # ---- synthref: Master(tempo) + the used synths ----
        editor_to_slot = {c['editor']: slot for slot, c in SYNTH_SLOTS.items()}
        for b in machine_blocks(self.syn):
            lib, nm = lib_of(b), name_of(b)
            if lib == 'Master':
                self.blocks.append(b.replace('<Patterns />', PAT, 1))
                self.seqs.append(('Master', [(0, total, '00')]))
            elif nm == '_x0001_pe1':
                self.blocks.append(set_data(b, build_blob_cols(
                    'Master', '00', 3, {1: [(0, s.bpm)], 2: [(0, s.tpb)]})))
                self.editors.append('_x0001_pe1')
            elif lib in _SYNTH_LIBS:                   # a synth generator (named by slot)
                if nm in used_synths:
                    self.blocks.append(set_track_count(set_patterns(b, PAT),
                                                       SYNTH_SLOTS[nm]['tracks']))
                    self.blocks[-1] = set_position(self.blocks[-1], *_SYNTH_POS[nm])
                    self.seqs.append((nm, [(0, total, '00')]))
            elif nm in editor_to_slot:                 # a synth editor
                slot = editor_to_slot[nm]
                if slot in used_synths:
                    c = SYNTH_SLOTS[slot]
                    ev = {} if slot in triggers0 else \
                        {(t, c['tcols'][0]): [(0, NOTE_OFF)] for t in range(c['tracks'])}
                    self.blocks.append(set_data(b, build_blob_mt(slot, '00', c['tcols'],
                                                                 c['tracks'], ev)))
                    self.editors.append(nm)
            else:
                self.blocks.append(b)

        # ---- drums (Plaits, per-section patterns) ----
        dgen = {name_of(b): b for b in machine_blocks(self.drm) if lib_of(b) == 'Pedal Plaits'}
        dped = {name_of(b): b for b in machine_blocks(self.drm)
                if lib_of(b) == 'Modern Pattern Editor'}
        DRUM_OLDPE = {'Kick': '_x0001_pe2', 'Snare': '_x0001_pe3',
                      'HatClosed': '_x0001_pe4', 'HatOpen': '_x0001_pe5'}
        drum_used = []
        for slot in DRUM_SLOTS:
            present = [(nm, dv.rows(slot, nm, sec_bars[nm], bar)) for nm in order
                       for dv in drum_voices]
            pats = [(nm, ev) for nm, ev in present if ev]
            if not pats:
                continue
            drum_used.append(slot)
            ped = self.pe()
            blobpats = [dict(name=nm, ncols=14, notecol=12, events=ev) for nm, ev in pats]
            seen = {nm for nm, _ in pats}
            plc = [(start * bar, sec_bars[nm] * bar, nm) for nm, start in arrange if nm in seen]
            gb = set_position(set_patterns(set_editor(dgen[slot], ped),
                              patterns_xml([(nm, sec_bars[nm] * bar) for nm, _ in pats])), *_DRUM_POS[slot])
            self.blocks.append(gb)
            self.blocks.append(set_data(set_name(dped[DRUM_OLDPE[slot]], DRUM_OLDPE[slot], ped),
                                        build_blob(slot, blobpats)))
            self.editors.append(ped)
            self.seqs.append((slot, plc))

        # ---- Pedal Chords (one per synth voice) ----
        for v in synth_voices:
            pcname = v.slot + 'Ctrl'
            ped = self.pe()
            pats, blobpats = [], []
            for nm in order:
                ce = v.colevents(nm, s._sections[nm].roots, s.scale, bar)
                if ce is None:
                    continue
                col0 = ce.get(0, [])
                if not any(r == 0 for r, _ in col0):           # §12.9 entry note-off
                    ce = {**ce, 0: [(0, NOTE_OFF)] + list(col0)}
                pats.append((nm, sec_bars[nm] * bar)); blobpats.append((nm, 14, ce))
            seen = {nm for nm, _ in pats}
            plc = [(start * bar, sec_bars[nm] * bar, nm) for nm, start in arrange if nm in seen]
            gb = set_position(set_data(set_patterns(set_editor(
                    set_name(self.PDLCHRD, 'PdlChrd', pcname), ped), patterns_xml(pats)),
                    pedal_chord_state(v.slot, 0)), *_CHORD_POS[v.slot])
            self.blocks.append(gb)
            self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                        build_blob_cols_multi(pcname, blobpats)))
            self.editors.append(ped)
            self.seqs.append((pcname, plc))

        # ---- Presetter (optional) ----
        if s._presets:
            items = [(slot, idx) for slot, idx in s._presets.items() if slot in used_synths]
            ped = self.pe()
            targets = [slot for slot, _ in items]
            ev = {(i, 0): [(i, idx)] for i, (_, idx) in enumerate(items)}
            pb = set_position(presetter_clear_stored_presets(set_track_count(set_data(set_patterns(
                set_editor(set_name(self.PRESETTER, 'Presetter', 'Presets'), ped), PAT),
                presetter_state(targets)), len(items)), len(items)), 0.4, 0.7)
            self.blocks.append(pb)
            self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                        build_blob_mt('Presets', '00', [0], len(items), ev)))
            self.editors.append(ped)
            self.seqs.append(('Presets', [(0, total, '00')]))

        # ---- submix buses ----
        conns = list(self.editors)
        if drum_used:
            conns += self._bus('DrumBus', PAT, total, (-0.95, -0.3),
                               [(d, db_to_amp(s._mix[d]) if d in s._mix else 16384) for d in drum_used])
        if used_synths:
            order_syn = [v.slot for v in synth_voices]
            conns += self._bus('SynthBus', PAT, total, (-0.55, -0.3),
                               [(slot, db_to_amp(s._mix[slot]) if slot in s._mix else 16384)
                                for slot in order_syn])

        # ---- finalise ----
        seq_order = (['Master'] + drum_used + [v.slot for v in synth_voices]
                     + [v.slot + 'Ctrl' for v in synth_voices]
                     + (['Presets'] if s._presets else []) + ['DrumBus', 'SynthBus'])
        self.seqs.sort(key=lambda mp: seq_order.index(mp[0]) if mp[0] in seq_order else 999)
        out = splice(self.syn, machines_xml(self.blocks),
                     connections_xml_multi(conns), sequences_xml_multi(self.seqs))
        out = set_loop_song_end(out, total)
        out = set_tempo(out, s.bpm, s.tpb)
        out = rename_song(out, 'synthref', s.name)
        out = clear_held_notes(out)
        return assert_valid(out)

    def _bus(self, name, PAT, total, pos, inputs):
        ped = self.pe()
        gb = set_param(set_patterns(set_editor(set_name(self.GAIN, 'PGainMul', name), ped), PAT),
                       'Amp', 16384)
        for ch, (src, amp) in enumerate(inputs):
            if amp != 16384:
                gb = set_param_track(gb, 'Amp', ch, amp)
        self.blocks.append(set_position(gb, *pos))
        self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                    build_blob_cols(name, '00', 8, {})))
        self.seqs.append((name, [(0, total, '00')]))
        return ([(src, name, amp, 16384, 0, ch) for ch, (src, amp) in enumerate(inputs)]
                + [name, ped])
