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
import re
from .theory import Scale, chord_code, arp_mode, parse_note
from .blob import (note_value as nv, NOTE_OFF, note_value,
                   build_blob, build_blob_mt, build_blob_cols, build_blob_cols_multi)
from .blocks import (read, machine_blocks, name_of, lib_of, find_machine, pattern_xml, patterns_xml,
                     set_patterns, set_data, set_track_count, set_position, set_name,
                     set_editor, set_param, set_param_track, set_input_tracks)
from .control import pedal_chord_state, presetter_state, presetter_clear_stored_presets
from .song import (machines_xml, connections_xml_multi, sequences_xml_multi, splice,
                   set_loop_song_end, set_tempo, rename_song, clear_held_notes, write_bmxml)
from .validate import assert_valid

HIT = 65                                              # Plaits trigger (C-4)
STOP_PAT = '_stop'        # reserved chord pattern name: one note-off, releases the target
STOP_ROWS = 1             # length (rows) of the stop pattern
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


_SWING_DIV = {'8th': 2, '8': 2, 'eighth': 2, '16th': 4, '16': 4, 'sixteenth': 4}


def swing_rows(rows, beat_rows, swing=50, subdivision='8th'):
    """Shuffle a set of straight row-offsets by delaying the *off-beats* of a
    subdivision. `swing` is a DAW-style percentage: 50 = straight (returned
    unchanged), ~67 = triplet shuffle, 75 = hard dotted feel. `subdivision` is
    '8th' (default) or '16th'.

    Only hits that land exactly on an off-beat of the subdivision move — the
    'and' of each beat for 8th-swing. Downbeats, backbeats and anything off the
    subdivision grid stay put, so the whole kit can share one `swing` value
    without smearing the kick or the backbeat. At 8 rows/beat, straight eighths
    0,4,8,12,16,20,24,28 at swing 67 become 0,5,8,13,16,21,24,29."""
    if swing == 50:
        return list(rows)
    div = _SWING_DIV.get(str(subdivision).lower())
    if div is None:
        raise ValueError('subdivision must be 8th or 16th, got %r' % (subdivision,))
    if beat_rows % div:
        raise ValueError('a %d-row beat does not divide into %s notes' % (beat_rows, subdivision))
    unit = beat_rows // div                       # rows per swung subdivision
    delay = round((swing - 50) / 50.0 * unit)     # rows added to each off-beat
    return [r + delay if (r % (2 * unit)) == unit else r for r in rows]


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
    """Block chords. `rhythm` is a one-bar step-string of strike positions, or a
    {section: step-string} dict for a per-section rhythm (a section absent from
    the dict is silent — handy for stabs that change figure between parts)."""
    def __init__(self, slot, octave, chord='maj', rhythm='x', octaves=1, sections=None):
        super().__init__(slot, octave, sections)
        self.code = chord_code(chord)
        self.rhythm = rhythm
        self.octaves = octaves

    def colevents(self, section, roots, scale, bar):
        if not self.active(section):
            return None
        rhythm = self.rhythm
        if isinstance(rhythm, dict):                 # per-section rhythm; absent => silent
            rhythm = rhythm.get(section)
            if not rhythm:
                return None
        rows = steps_to_rows(rhythm, bar)
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

    def __init__(self, patterns, swing=50, subdivision='8th'):
        """`patterns` = {drum_slot: step-string | {section: step-string}}.
        `swing` (DAW-style %, 50 = straight) and `subdivision` ('8th'/'16th')
        shuffle the off-beats of every slot — see swing_rows()."""
        bad = set(patterns) - set(DRUM_SLOTS)
        if bad:
            raise ValueError('unknown drum slot(s) %s (have %s)' % (bad, ', '.join(DRUM_SLOTS)))
        self.patterns = patterns
        self.swing = swing
        self.subdivision = subdivision

    def rows(self, slot, section, bars, bar):
        spec = self.patterns.get(slot)
        if spec is None:
            return None
        s = spec.get(section) if isinstance(spec, dict) else spec
        if not s:
            return None
        base = swing_rows(steps_to_rows(s, bar), bar // 4, self.swing, self.subdivision)
        return [(b * bar + r, HIT) for b in range(bars) for r in base]


_TOKEN = re.compile(r'^([A-Ga-g][#b]?)(-?\d+)?$')


class Melody:
    """A real, monophonic melodic line written straight into a synth's pattern
    (note-ons + note-offs), with no Pedal Chord. `phrases` maps a section name to
    a list of (step, note, length): `step` and `length` are in grid units (16th
    notes by default, so 16 steps per bar), counted from the start of the
    section; `note` is a token like 'A5', 'C#6', 'Eb5', or bare 'A' (which uses
    the voice's default `octave`). Targets an extra synth registered with
    Song.synth() -- not one of the four synthref slots."""
    is_synth = False
    is_melody = True

    def __init__(self, slot, octave=5, phrases=None, grid=16, sections=None):
        self.slot = slot
        self.octave = octave
        self.phrases = phrases or {}
        self.grid = grid
        self.sections = set(sections) if sections else None

    def active(self, section):
        if self.sections is not None and section not in self.sections:
            return False
        return bool(self.phrases.get(section))

    def _pitch(self, token):
        m = _TOKEN.match(token.strip())
        if not m:
            raise ValueError('bad note token %r (want e.g. A5, C#6, Eb5, or A)' % token)
        octv = int(m.group(2)) if m.group(2) is not None else self.octave
        return note_value(octv, parse_note(m.group(1)))

    def column_events(self, arrange, bar, total):
        """Resolve phrases over the arrangement into (row, value) note events for
        the synth's note column. On a mono synth a fresh note-on cuts the
        previous note, so note-offs are emitted only at rests / phrase ends /
        the start of a silent section -- never where a new note retriggers."""
        if bar % self.grid:
            raise ValueError('grid %d must divide the bar (%d rows)' % (self.grid, bar))
        rps = bar // self.grid
        ons, offs = [], set()
        for nm, start in arrange:
            base = start * bar
            if self.active(nm):
                for step, token, length in self.phrases[nm]:
                    ons.append((base + step * rps, self._pitch(token)))
                    offs.add(base + (step + length) * rps)      # natural release
            else:
                offs.add(base)                                  # release entering a silent section
        on_rows = {r for r, _ in ons}
        offs = {r for r in offs if r not in on_rows and 0 <= r < total}
        return sorted(ons + [(r, NOTE_OFF) for r in offs])


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
        self._limiter = None
        self._extra_synths = []
        self.refs = refs

    def section(self, name, roots, bars=None):
        self._sections[name] = Section(name, roots, bars)
        return self

    def add(self, voice):
        self._voices.append(voice)
        return self

    def synth(self, name, library, note_col, tracks=1):
        """Register an extra synth (spliced from MachineRef by Library) to host a
        Melody -- e.g. s.synth('Lead2', 'Pedal FM', note_col=42). It routes through
        its own Pedal Gain and accepts mix()/presets() like the built-in slots."""
        self._extra_synths.append(dict(name=name, library=library,
                                       note_col=note_col, tracks=tracks))
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

    def limiter(self, ceiling=-1.0, isp=True):
        """Add a Pedal Limit as the final machine before Master: the drum bus and
        every per-synth gain feed it, it feeds Master. Transparent by default —
        Threshold and Output are both set to `ceiling` dBFS (no makeup gain), so it
        only catches peaks. `isp` enables 4x true-peak (inter-sample) detection."""
        self._limiter = dict(ceiling=ceiling, isp=isp)
        return self

    # -- compile -------------------------------------------------------------
    def compile(self):
        return _Compiler(self).run()

    def write(self, path):
        n = write_bmxml(path, self.compile())
        return n


# ---- one-call commission entry point ---------------------------------------

def _voice_from_spec(v):
    """Map one voice dict to a voice object. Fields mirror the voice classes."""
    t = v.get('type')
    if t == 'chords':
        return Chords(v['slot'], v['octave'], v.get('chord', 'maj'),
                      v.get('rhythm', 'x'), v.get('octaves', 1), v.get('sections'))
    if t == 'arp':
        return Arp(v['slot'], v['octave'], v.get('chord', 'maj'), v.get('mode', 'up'),
                   v.get('speed', 4), v.get('octaves', 2), v.get('swing', 0), v.get('sections'))
    if t == 'drums':
        return Drums(v['patterns'], v.get('swing', 50), v.get('subdivision', '8th'))
    if t == 'melody':
        phrases = {k: [tuple(n) for n in ph] for k, ph in (v.get('phrases') or {}).items()}
        return Melody(v['slot'], v.get('octave', 5), phrases, v.get('grid', 16), v.get('sections'))
    raise ValueError('unknown voice type %r' % (t,))


def compose(spec):
    """Build a Song from a single declarative spec dict — the 'spec -> song' goal
    (BMXML §13) as one call, JSON-serialisable end to end.

    Spec keys (all but `name` optional):
      name, bpm, tpb, key, scale, refs   — the Song header
      sections   {name: [roots...]}  or  {name: {'roots': [...], 'bars': N}}
      arrange    [section_name, ...]      — placement order on the timeline
      synths     [{name, library, note_col, tracks}]   — extra synths for melodies
      voices     [{type: 'chords'|'arp'|'drums'|'melody', ...}]   — fields per class
      mix        {slot: dB}
      presets    {slot: bank_index}
      limiter    {ceiling, isp}

    Returns an un-compiled Song; call `.compile()` or `.write(path)`."""
    s = Song(spec['name'], bpm=spec.get('bpm', 125), tpb=spec.get('tpb', 8),
             key=spec.get('key', 'C'), scale=spec.get('scale', 'major'),
             refs=spec.get('refs'))
    for name, sec in spec.get('sections', {}).items():
        if isinstance(sec, dict):
            s.section(name, sec['roots'], sec.get('bars'))
        else:
            s.section(name, sec)
    for es in spec.get('synths', []):
        s.synth(es['name'], es['library'], es['note_col'], es.get('tracks', 1))
    for v in spec.get('voices', []):
        s.add(_voice_from_spec(v))
    if spec.get('arrange'):
        s.arrange(spec['arrange'])
    if spec.get('mix'):
        s.mix(**spec['mix'])
    if spec.get('presets'):
        s.presets(**spec['presets'])
    if spec.get('limiter'):
        s.limiter(**spec['limiter'])
    return s


class _Compiler:
    def __init__(self, song):
        self.s = song
        self.bar = song.bar
        here = os.path.dirname(os.path.abspath(__file__))
        refs = song.refs or os.environ.get('REBUZZ_REFS') or os.path.join(here, '..', '..', 'refs')
        self.refs_dir = refs
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
        self.PLIM = None                               # lazily loaded if a limiter is requested
        self.GAIN1 = None                              # single Pedal Gain (per-synth), lazily loaded
        self.mref = None                               # lazily loaded if extra synths are used
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
        if STOP_PAT in s._sections:
            raise ValueError('section name %r is reserved' % STOP_PAT)
        used_synths = {v.slot for v in synth_voices}
        if len(used_synths) != len(synth_voices):
            raise ValueError('each synth slot may host only one voice')

        # A control-driven target is released two ways at every section where it
        # should fall silent (belt and braces): (1) a note-off on the target's
        # OWN pattern releases the voice that is actually sounding -- essential
        # when the patch has a long release/sustain, which the control machine
        # cannot shorten once it has triggered the note; and (2) a stop pattern
        # on its Pedal Chord halts any further triggers (added in the chord loop
        # below). Both fire at the same rows: the start of each silent section.
        def plays(v, sec):
            return v.colevents(sec, s._sections[sec].roots, s.scale, bar) is not None
        nm0 = arrange[0][0]

        def triggered_at_0(v):                         # does v strike a note on song row 0?
            ce = v.colevents(nm0, s._sections[nm0].roots, s.scale, bar)
            return ce is not None and any(r == 0 for r, _ in ce.get(0, []))
        stop_rows = {}
        for v in synth_voices:
            rows = set(st * bar for nm, st in arrange if not plays(v, nm))
            if not triggered_at_0(v):                   # silent OR first hit is mid-bar:
                rows.add(0)                             # release on the loop wrap (§12.9.1)
            stop_rows[v.slot] = sorted(rows)

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
            elif nm in editor_to_slot:                 # a synth editor: note-off where it falls silent
                slot = editor_to_slot[nm]
                if slot in used_synths:
                    c = SYNTH_SLOTS[slot]
                    offs = stop_rows.get(slot, [])
                    ev = {(t, c['tcols'][0]): [(r, NOTE_OFF) for r in offs]
                          for t in range(c['tracks'])} if offs else {}
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
            # Companion to the target's own note-offs (above): a short stop
            # pattern (one note-off in col 0) sequenced at the start of every
            # silent section halts further triggers. The target note-off frees
            # the sounding voice; this stops the arp from re-triggering. Together
            # they cover entry, mid-song exits, and the loop wrap.
            if any(nm not in seen for nm, _ in arrange):
                pats.append((STOP_PAT, STOP_ROWS))
                blobpats.append((STOP_PAT, 14, {0: [(0, NOTE_OFF)]}))
            plc = []
            for nm, start in arrange:
                if nm in seen:
                    plc.append((start * bar, sec_bars[nm] * bar, nm))
                else:
                    plc.append((start * bar, STOP_ROWS, STOP_PAT))
            gb = set_position(set_data(set_patterns(set_editor(
                    set_name(self.PDLCHRD, 'PdlChrd', pcname), ped), patterns_xml(pats)),
                    pedal_chord_state(v.slot, 0)), *_CHORD_POS[v.slot])
            self.blocks.append(gb)
            self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                        build_blob_cols_multi(pcname, blobpats)))
            self.editors.append(ped)
            self.seqs.append((pcname, plc))

        # ---- extra synths (direct-note melodies, spliced from MachineRef) ----
        melody_voices = [v for v in s._voices if getattr(v, 'is_melody', False)]
        extra_names = []
        if s._extra_synths:
            if self.mref is None:
                self.mref = read(os.path.join(self.refs_dir, 'MachineRef.bmxml'))
            extra_pos = [(0.45, 0.25), (0.45, -0.05), (-0.85, 0.25), (-0.85, -0.05)]
            taken = {es['name'] for es in s._extra_synths}
            if taken & (set(SYNTH_SLOTS) | set(DRUM_SLOTS)):
                raise ValueError('extra synth name collides with a built-in slot')
            for i, es in enumerate(s._extra_synths):
                name = es['name']; extra_names.append(name)
                gen = find_machine(self.mref, es['library'])
                if gen is None:
                    raise ValueError('machine %r not in MachineRef' % es['library'])
                ped = self.pe()
                gb = set_position(set_track_count(set_patterns(set_editor(
                        set_name(gen, name_of(gen), name), ped), PAT), es['tracks']),
                        *extra_pos[i % len(extra_pos)])
                self.blocks.append(gb)
                mv = next((v for v in melody_voices if v.slot == name), None)
                col = {(0, es['note_col']): mv.column_events(arrange, bar, total)} if mv else {}
                self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                            build_blob_mt(name, '00', [es['note_col']],
                                                          es['tracks'], col)))
                self.editors.append(ped)
                self.seqs.append((name, [(0, total, '00')]))
        bad = [v.slot for v in melody_voices if v.slot not in extra_names]
        if bad:
            raise ValueError('Melody slot(s) %s have no Song.synth() registration' % bad)

        # ---- Presetter (optional) ----
        if s._presets:
            valid = used_synths | set(extra_names)
            items = [(slot, idx) for slot, idx in s._presets.items() if slot in valid]
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

        # ---- submix: drums on one Gain Multi, each synth on its own Pedal Gain ----
        # Per-synth gains give a separate recordable output node per synth (stems)
        # and sum into the limiter (or Master) exactly as a shared bus would.
        order_syn = [v.slot for v in synth_voices] + extra_names
        conns = list(self.editors)
        dest = 'Limit' if s._limiter else 'Master'
        if drum_used:
            conns += self._bus('DrumBus', PAT, total, (-0.95, -0.3),
                               [(d, db_to_amp(s._mix[d]) if d in s._mix else 16384) for d in drum_used],
                               dest=dest)
        gain_pos = [(-0.5, -0.15), (-0.2, -0.15), (0.1, -0.15), (0.4, -0.15), (0.7, -0.15),
                    (-0.5, -0.45), (-0.2, -0.45), (0.1, -0.45), (0.4, -0.45), (0.7, -0.45)]
        for i, slot in enumerate(order_syn):
            amp = db_to_amp(s._mix[slot]) if slot in s._mix else 16384
            conns += self._gain('%sGain' % slot, PAT, total, gain_pos[i % len(gain_pos)],
                                 slot, amp, dest)
        if s._limiter:
            conns += self._limiter_block('Limit', PAT, total, (-0.75, -0.62),
                                         s._limiter['ceiling'], s._limiter['isp'])

        # ---- finalise ----
        seq_order = (['Master'] + drum_used + [v.slot for v in synth_voices] + extra_names
                     + [v.slot + 'Ctrl' for v in synth_voices]
                     + (['Presets'] if s._presets else []) + ['DrumBus']
                     + ['%sGain' % slot for slot in order_syn]
                     + (['Limit'] if s._limiter else []))
        self.seqs.sort(key=lambda mp: seq_order.index(mp[0]) if mp[0] in seq_order else 999)
        out = splice(self.syn, machines_xml(self.blocks),
                     connections_xml_multi(conns), sequences_xml_multi(self.seqs))
        out = set_loop_song_end(out, total)
        out = set_tempo(out, s.bpm, s.tpb)
        out = rename_song(out, 'synthref', s.name)
        out = clear_held_notes(out)
        return assert_valid(out)

    def _gain(self, name, PAT, total, pos, src, amp, dest):
        """One synth -> its own Pedal Gain -> `dest` (limiter or Master). The
        synth's mix trim sits on the Gain's single input Amp (16384 = unity),
        kept equal on the connection -- same scheme as a Gain Multi channel, but
        each synth now has a dedicated, recordable output node for stems."""
        if self.GAIN1 is None:
            if self.mref is None:
                self.mref = read(os.path.join(self.refs_dir, 'MachineRef.bmxml'))
            self.GAIN1 = find_machine(self.mref, 'Pedal Gain')
        ped = self.pe()
        gb = set_input_tracks(set_name(self.GAIN1, name_of(self.GAIN1), name), 1)
        gb = set_param(set_patterns(set_editor(gb, ped), PAT), 'Amp', amp)
        self.blocks.append(set_position(gb, *pos))
        self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                    build_blob_cols(name, '00', 3, {})))   # Gain/Mute/Inertia
        self.seqs.append((name, [(0, total, '00')]))
        out = name if dest == 'Master' else (name, dest, 16384, 16384, 0, 0)
        return [(src, name, amp, 16384, 0, 0), out, ped]

    def _bus(self, name, PAT, total, pos, inputs, dest='Master'):
        ped = self.pe()
        gb = set_input_tracks(set_name(self.GAIN, 'PGainMul', name), len(inputs))
        gb = set_param(set_patterns(set_editor(gb, ped), PAT), 'Amp', 16384)
        for ch, (src, amp) in enumerate(inputs):
            if amp != 16384:
                gb = set_param_track(gb, 'Amp', ch, amp)
        self.blocks.append(set_position(gb, *pos))
        self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                    build_blob_cols(name, '00', 8, {})))
        self.seqs.append((name, [(0, total, '00')]))
        bus_out = name if dest == 'Master' else (name, dest, 16384, 16384, 0, 0)
        return ([(src, name, amp, 16384, 0, ch) for ch, (src, amp) in enumerate(inputs)]
                + [bus_out, ped])

    def _limiter_block(self, name, PAT, total, pos, ceiling, isp):
        """Splice a Pedal Limit before Master. Threshold == Output == `ceiling`
        (no makeup gain) = a transparent peak ceiling; buses sum at channel 0."""
        if self.PLIM is None:
            lmt = read(os.path.join(self.refs_dir, 'limitref.bmxml'))
            self.PLIM = next(b for b in machine_blocks(lmt) if lib_of(b) == 'Pedal Limit')
        ped = self.pe()
        step = round(-ceiling * 10)                    # -0.1 dB/step; 0 = 0 dBFS
        lm = set_name(self.PLIM, name_of(self.PLIM), name)
        lm = set_patterns(set_editor(lm, ped), PAT)
        lm = set_param(lm, 'Threshold', step)
        lm = set_param(lm, 'Output_x0020_Level', step)
        lm = set_param(lm, 'ISP', 1 if isp else 0)
        self.blocks.append(set_position(lm, *pos))
        self.blocks.append(set_data(set_name(self.MPE, '_x0001_pe3', ped),
                                    build_blob_cols(name, '00', 3, {})))
        self.seqs.append((name, [(0, total, '00')]))
        return [name, ped]                             # Limit -> Master ; editor -> Master
