"""Tests for rebuzz.theory and rebuzz.dsl."""
import os, re, sys, base64, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from rebuzz import (Song, Chords, Arp, Drums, Melody, validate, decode_blob,
                    Scale, parse_note, chord_code, arp_mode, steps_to_rows, db_to_amp)
from rebuzz.blocks import machine_blocks, lib_of, name_of


# --- theory ------------------------------------------------------------------

def test_note_parsing():
    assert (parse_note('C'), parse_note('A'), parse_note('Bb'), parse_note('F#')) == (0, 9, 10, 6)
    assert parse_note('B#') == 0


def test_scale_degrees():
    s = Scale('A', 'blues')
    assert [s.degree_index(d) % 12 for d in range(1, 7)] == [9, 0, 2, 3, 4, 7]
    assert s.index_of('D') == 2                       # absolute name overrides scale


def test_codes():
    assert (chord_code('dom7'), chord_code('maj'), chord_code('oct')) == (2, 0, 50)
    assert (arp_mode('up'), arp_mode('updown'), arp_mode('block')) == (1, 3, 0)


def test_steps_to_rows():
    assert steps_to_rows('x...x...x...x...', 32) == [0, 8, 16, 24]
    assert steps_to_rows('xxxxxxxx', 32) == [0, 4, 8, 12, 16, 20, 24, 28]
    assert db_to_amp(0) == 16384 and db_to_amp(-15) == 2914


# --- compile -----------------------------------------------------------------

def _demo():
    s = Song('T', bpm=90, tpb=8, key='A', scale='blues')
    s.section('Verse', ['A', 'A', 'D', 'E']); s.section('Chorus', ['D', 'D', 'A', 'E'])
    s.add(Arp('Bass', octave=2, chord='dom7', mode='up', speed=8, octaves=2))
    s.add(Chords('Pad', octave=4, chord='dom7'))
    s.add(Chords('Comp', octave=3, chord='dom7', rhythm='x...x...x...x...', sections=['Chorus']))
    s.add(Drums({'Kick': 'x.......x.......', 'HatClosed': 'xxxxxxxx'}))
    s.arrange(['Verse', 'Chorus', 'Verse']); s.mix(Pad=-15)
    return s


def test_compile_validates():
    assert validate(_demo().compile()).ok


def test_unused_slots_dropped():
    names = {n for b in machine_blocks(_demo().compile())
             for n in [re.search(r'<Name>(.*?)</Name>', b).group(1)]}
    assert 'Bass' in names and 'Lead' not in names and 'Snare' not in names


def _editor_events(xml):
    ev = {}
    for b in machine_blocks(xml):
        if lib_of(b) == 'Modern Pattern Editor':
            d = decode_blob(base64.b64decode(re.search(r'<Data>([A-Za-z0-9+/=]+)</Data>', b).group(1)))
            if d:
                ev[d['mname']] = d['patterns']
    return ev


def _placements(xml, machine):
    for sq in re.findall(r'<Sequence>.*?</Sequence>', xml, re.S):
        if re.search(r'<Machine>(.*?)</Machine>', sq).group(1) != machine:
            continue
        return sorted((int(re.search(r'<Time>(\d+)</Time>', e).group(1)),
                       re.search(r'<Pattern>(.*?)</Pattern>', e).group(1))
                      for e in re.findall(r'<Event>.*?</Event>', sq, re.S))
    return []


def test_loop_safety_applied():
    # both mechanisms at every silent section: a note-off on the target's own
    # pattern (cuts a long release) AND a stop pattern on its Pedal Chord.
    xml = _demo().compile()
    comp_stops = sorted(t for t, p in _placements(xml, 'CompCtrl') if p == '_stop')
    assert comp_stops == [0, 256]                       # Comp (chorus-only) stopped in both verses
    ev = _editor_events(xml)
    comp_offs = sorted({r for es in ev['Comp']['00'].values() for r, v in es if v == 255})
    assert comp_offs == comp_stops                      # target note-offs coincide with chord stops
    # Bass/Pad play every section -> re-trigger, so neither a stop nor a note-off
    assert all(p != '_stop' for _, p in _placements(xml, 'BassCtrl'))
    assert all(v != 255 for es in ev['Bass']['00'].values() for r, v in es)


def test_mix_trim_on_its_own_gain():
    # each synth now has its own Pedal Gain; the trim sits on that gain's input
    # Amp (machine + connection, kept equal), not on a shared bus channel.
    xml = _demo().compile()
    pad = [b for b in machine_blocks(xml)
           if lib_of(b) == 'Pedal Gain' and re.search(r'<Name>PadGain</Name>', b)][0]
    ig = re.search(r'<ParameterGroup>\s*<Type>Input</Type>.*?</ParameterGroup>', pad, re.S).group(0)
    amp = [p for p in re.findall(r'<Parameter>.*?</Parameter>', ig, re.S) if '<Name>Amp</Name>' in p][0]
    val = dict((int(t), int(v)) for t, v in
               re.findall(r'<Track>(\d+)</Track>\s*<Value>(-?\d+)</Value>', amp))
    assert val == {0: 2914}                                # -15 dB on PadGain only
    # an untrimmed synth's gain stays unity
    bass = [b for b in machine_blocks(xml)
            if lib_of(b) == 'Pedal Gain' and re.search(r'<Name>BassGain</Name>', b)][0]
    bamp = re.search(r'<Track>0</Track>\s*<Value>(-?\d+)</Value>', bass).group(1)
    assert bamp == '16384'


def test_synths_route_through_own_gain_to_dest():
    # no synth Gain Multi remains; each synth -> its Pedal Gain -> dest
    xml = _demo().compile()
    gm = [name_of(b) for b in machine_blocks(xml) if lib_of(b) == 'Pedal Gain Multi']
    assert gm == ['DrumBus']                               # only drums keep a multi
    pg = sorted(name_of(b) for b in machine_blocks(xml) if lib_of(b) == 'Pedal Gain')
    assert pg == ['BassGain', 'CompGain', 'PadGain']       # one per synth slot (_demo has no limiter)
    conns = re.findall(r'<MachineConnection>.*?</MachineConnection>', xml, re.S)

    def edge(src):
        for c in conns:
            if re.search(r'<Source>%s</Source>' % src, c):
                return re.search(r'<Destination>(.*?)</Destination>', c).group(1)
    assert edge('Pad') == 'PadGain' and edge('PadGain') == 'Master'   # no limiter in _demo


def test_demo_build_determinism():
    path = os.path.join(ROOT, 'songs', 'DslDemo.bmxml')
    subprocess.run([sys.executable, os.path.join(ROOT, 'src', 'build_dsl_demo.py')],
                   check=True, capture_output=True)
    a = open(path, 'rb').read()
    subprocess.run([sys.executable, os.path.join(ROOT, 'src', 'build_dsl_demo.py')],
                   check=True, capture_output=True)
    assert a == open(path, 'rb').read()


def test_per_section_chord_rhythm():
    # a dict rhythm is silent in sections it omits, and uses the named figure elsewhere
    c = Chords('Comp', octave=3, chord='dom7', rhythm={'Verse': 'x.x.x.x.', 'Chorus': 'x.......'})
    sc = Scale('A', 'blues')
    assert c.colevents('Intro', ['A'], sc, 32) is None            # omitted -> silent
    ce_v = c.colevents('Verse', ['A'], sc, 32)
    assert [r for r, _ in ce_v[0]] == [0, 8, 16, 24]              # 8-step -> every 4 rows, 4 hits
    ce_c = c.colevents('Chorus', ['A'], sc, 32)
    assert [r for r, _ in ce_c[0]] == [0]                         # single downbeat


def test_limiter_in_dsl():
    s = (Song('LimTest', bpm=90, tpb=8, key='A', scale='blues')
         .section('A', ['A', 'D', 'E', 'A'])
         .add(Arp('Bass', octave=2, chord='dom7'))
         .add(Drums({'Kick': 'x...x...'}))
         .arrange(['A'])
         .limiter(ceiling=-1.0, isp=True))
    xml = s.compile()                                             # runs assert_valid
    libs = [lib_of(b) for b in machine_blocks(xml)]
    assert 'Pedal Limit' in libs
    # drums via their bus and the synth via its own Pedal Gain both feed the limiter
    assert re.search(r'<Source>DrumBus</Source>\s*<Destination>Limit</Destination>', xml)
    assert re.search(r'<Source>BassGain</Source>\s*<Destination>Limit</Destination>', xml)
    assert re.search(r'<Source>Limit</Source>\s*<Destination>Master</Destination>', xml)
    # transparent: Threshold and Output both at the -1.0 dB ceiling (value 10)
    lim = next(b for b in machine_blocks(xml) if lib_of(b) == 'Pedal Limit')
    assert lim.count('<Value>10</Value>') >= 2


def test_swing_rows():
    from rebuzz import swing_rows
    straight = [0, 4, 8, 12, 16, 20, 24, 28]
    assert swing_rows(straight, 8, 50) == straight              # 50 = straight, no-op
    assert swing_rows(straight, 8, 67) == [0, 5, 8, 13, 16, 21, 24, 29]   # triplet = hand-tuned hats
    assert swing_rows([0, 8, 16, 24], 8, 67) == [0, 8, 16, 24]  # downbeats/backbeat untouched
    assert swing_rows(straight, 8, 75) == [0, 6, 8, 14, 16, 22, 24, 30]   # hard shuffle
    assert swing_rows([0, 2, 4, 6], 8, 67, '16th') == [0, 3, 4, 7]        # 16th off-beats


def test_drums_swing_applied():
    sc = Scale('A', 'blues')
    straight = Drums({'HatClosed': 'xxxxxxxx'})
    swung = Drums({'HatClosed': 'xxxxxxxx'}, swing=67)
    rs = [r for r, _ in straight.rows('HatClosed', 'V', 1, 32)]
    rw = [r for r, _ in swung.rows('HatClosed', 'V', 1, 32)]
    assert rs == [0, 4, 8, 12, 16, 20, 24, 28]
    assert rw == [0, 5, 8, 13, 16, 21, 24, 29]


def test_voice_exit_release():
    # a control-driven voice active only in a middle section is released both by
    # a note-off on its own synth (cuts the sustaining voice) AND by a stop
    # pattern on its Pedal Chord (halts triggers), at the same silent rows.
    import base64
    from rebuzz import decode_blob
    s = (Song('Exit', bpm=90, tpb=8, key='A', scale='blues')
         .section('A', ['A', 'A', 'A', 'A'])
         .section('B', ['D', 'D', 'D', 'D'])
         .add(Arp('Bass', octave=2, chord='dom7'))                  # tick-0 anchor, never exits
         .add(Arp('Lead', octave=5, chord='dom7', sections=['B']))  # only in B
         .arrange(['A', 'B', 'A']))                                 # B sandwiched between A's
    xml = s.compile()
    # A=4 bars: A@row0, B@row128, A@row256. Stop in both A's (incl. row 0 for
    # entry/loop), B plays.
    assert _placements(xml, 'LeadCtrl') == [(0, '_stop'), (128, 'B'), (256, '_stop')]
    # and the Lead synth carries note-offs at the same silent rows
    lead_offs = None
    for b in machine_blocks(xml):
        if lib_of(b) != 'Modern Pattern Editor':
            continue
        m = re.search(r'<Data>([A-Za-z0-9+/=]+)</Data>', b)
        if not m:
            continue
        d = decode_blob(base64.b64decode(m.group(1)))
        if d and d.get('mname') == 'Lead':
            lead_offs = sorted({r for col in d['patterns'].get('00', {}).values()
                                for r, v in col if v == 255})
    assert lead_offs == [0, 256]                          # released at loop point and at the exit


def test_voice_stays_active_not_cut():
    # X -> Y, both lead-active and adjacent: neither a stop nor a note-off between
    import base64
    from rebuzz import decode_blob
    s = (Song('Cut', bpm=90, tpb=8, key='A', scale='blues')
         .section('I', ['A', 'A', 'A', 'A'])
         .section('X', ['D', 'D', 'D', 'D'])
         .section('Y', ['E', 'E', 'E', 'E'])
         .add(Arp('Bass', octave=2, chord='dom7'))
         .add(Arp('Lead', octave=5, chord='dom7', sections=['X', 'Y']))
         .arrange(['I', 'X', 'Y', 'I']))                  # lead spans X,Y adjacent
    xml = s.compile()
    # stop in I (row 0, entry/loop) and the trailing I; X and Y play with no stop between
    assert _placements(xml, 'LeadCtrl') == [(0, '_stop'), (128, 'X'), (256, 'Y'), (384, '_stop')]
    lead_offs = None
    for b in machine_blocks(xml):
        if lib_of(b) == 'Modern Pattern Editor':
            m = re.search(r'<Data>([A-Za-z0-9+/=]+)</Data>', b)
            d = m and decode_blob(base64.b64decode(m.group(1)))
            if d and d.get('mname') == 'Lead':
                lead_offs = sorted({r for col in d['patterns'].get('00', {}).values()
                                    for r, v in col if v == 255})
    assert lead_offs == [0, 384]                          # silent I's only; nothing between X and Y


def _melody_song():
    s = Song('M', bpm=90, tpb=8, key='A', scale='blues')
    s.section('Verse', ['A', 'A', 'D', 'E']); s.section('Chorus', ['D', 'D', 'A', 'E'])
    s.add(Chords('Pad', octave=4, chord='dom7'))
    s.synth('Lead2', 'Pedal FM', note_col=42, tracks=1)
    s.add(Melody('Lead2', octave=5, grid=16, phrases={
        'Verse': [(0, 'A5', 2), (4, 'C6', 2), (8, 'E5', 4)]}))   # silent in Chorus
    s.arrange(['Verse', 'Chorus', 'Verse']); s.presets(Lead2=15)
    return s


def test_melody_synth_spliced_and_routed():
    xml = _melody_song().compile()
    assert validate(xml).ok
    # the FM machine is present under the requested name
    assert any(lib_of(b) == 'Pedal FM' and name_of(b) == 'Lead2' for b in machine_blocks(xml))
    # routed through its own Pedal Gain (no limiter in this song -> on to Master)
    conns = re.findall(r'<MachineConnection>.*?</MachineConnection>', xml, re.S)
    lead2 = [c for c in conns if re.search(r'<Source>Lead2</Source>', c)]
    assert lead2 and re.search(r'<Destination>Lead2Gain</Destination>', lead2[0])
    assert any(lib_of(b) == 'Pedal Gain' and name_of(b) == 'Lead2Gain' for b in machine_blocks(xml))


def test_melody_notes_in_note_column_only():
    xml = _melody_song().compile()
    for b in machine_blocks(xml):
        if lib_of(b) == 'Modern Pattern Editor':
            m = re.search(r'<Data>([A-Za-z0-9+/=]+)</Data>', b)
            d = m and decode_blob(base64.b64decode(m.group(1)))
            if d and d.get('mname') == 'Lead2':
                cols = sorted(c for (t, c), es in d['patterns']['00'].items() if es)
                assert cols == [42]                          # notes only in FM's note column
                ons = [v for col in d['patterns']['00'].values() for r, v in col if v != 255]
                assert len(ons) == 6                         # 3 verse notes x 2 verse placements


def test_bus_grows_to_input_count():
    # DrumBus (Gain Multi) sizes its Input group to its drum count...
    xml = _melody_song().compile()       # 1 drum slot? -> use a multi-input drum song
    s = Song('B', bpm=90, tpb=8, key='A', scale='blues')
    s.section('V', ['A', 'A', 'D', 'E'])
    s.add(Drums({'Kick': 'x...x...', 'Snare': '..x...x.', 'HatClosed': 'xxxxxxxx'}))
    s.arrange(['V'])
    xml = s.compile()
    db = [b for b in machine_blocks(xml) if re.search(r'<Name>DrumBus</Name>', b)][0]
    ig = re.search(r'<ParameterGroup>\s*<Type>Input</Type>.*?</ParameterGroup>', db, re.S).group(0)
    tc = int(re.search(r'<TrackCount>(\d+)</TrackCount>', ig).group(1))
    nin = len([c for c in re.findall(r'<MachineConnection>.*?</MachineConnection>', xml, re.S)
               if re.search(r'<Destination>DrumBus</Destination>', c)])
    assert tc == nin == 3
    # ...and a single Pedal Gain sizes its Input group to exactly one track
    xml2 = _melody_song().compile()
    pg = [b for b in machine_blocks(xml2) if lib_of(b) == 'Pedal Gain'][0]
    ig2 = re.search(r'<ParameterGroup>\s*<Type>Input</Type>.*?</ParameterGroup>', pg, re.S).group(0)
    assert int(re.search(r'<TrackCount>(\d+)</TrackCount>', ig2).group(1)) == 1


def test_melody_slot_needs_registration():
    s = Song('X', bpm=90, tpb=8, key='A', scale='blues')
    s.section('Verse', ['A', 'A', 'D', 'E'])
    s.add(Melody('Ghost', phrases={'Verse': [(0, 'A5', 2)]}))   # no Song.synth('Ghost', ...)
    s.arrange(['Verse'])
    try:
        s.compile(); assert False, 'expected ValueError for unregistered Melody slot'
    except ValueError:
        pass


def _demo_spec():
    # the exact declarative twin of _demo()
    return {
        'name': 'T', 'bpm': 90, 'tpb': 8, 'key': 'A', 'scale': 'blues',
        'sections': {'Verse': ['A', 'A', 'D', 'E'], 'Chorus': ['D', 'D', 'A', 'E']},
        'voices': [
            {'type': 'arp', 'slot': 'Bass', 'octave': 2, 'chord': 'dom7',
             'mode': 'up', 'speed': 8, 'octaves': 2},
            {'type': 'chords', 'slot': 'Pad', 'octave': 4, 'chord': 'dom7'},
            {'type': 'chords', 'slot': 'Comp', 'octave': 3, 'chord': 'dom7',
             'rhythm': 'x...x...x...x...', 'sections': ['Chorus']},
            {'type': 'drums', 'patterns': {'Kick': 'x.......x.......', 'HatClosed': 'xxxxxxxx'}},
        ],
        'arrange': ['Verse', 'Chorus', 'Verse'],
        'mix': {'Pad': -15},
    }


def test_compose_matches_fluent():
    from rebuzz import compose
    assert compose(_demo_spec()).compile() == _demo().compile()    # byte-identical mapping


def test_compose_full_features():
    # one spec exercising every voice type + extra synth + melody + limiter + presets
    from rebuzz import compose
    spec = {
        'name': 'Full', 'bpm': 100, 'tpb': 8, 'key': 'A', 'scale': 'blues',
        'sections': {'A': ['A', 'A', 'D', 'E'], 'B': ['D', 'D', 'A', 'E']},
        'synths': [{'name': 'Lead2', 'library': 'Pedal FM', 'note_col': 42}],
        'voices': [
            {'type': 'arp', 'slot': 'Bass', 'octave': 2, 'chord': 'dom7'},
            {'type': 'chords', 'slot': 'Pad', 'octave': 4, 'chord': 'dom7'},
            {'type': 'chords', 'slot': 'Comp', 'octave': 3, 'chord': 'dom7',
             'rhythm': {'A': 'x.x.x.x.', 'B': 'x.......'}},
            {'type': 'drums', 'patterns': {'Kick': 'x...x...', 'Snare': '..x...x.'}, 'swing': 67},
            {'type': 'melody', 'slot': 'Lead2', 'octave': 5, 'grid': 16,
             'phrases': {'A': [[0, 'A5', 2], [4, 'C6', 2], [8, 'E5', 4]]}},
        ],
        'arrange': ['A', 'B', 'A'],
        'mix': {'Pad': -20}, 'presets': {'Bass': 0, 'Lead2': 15},
        'limiter': {'ceiling': -1.0, 'isp': True},
    }
    s = compose(spec)
    xml = s.compile()
    assert validate(xml).ok
    assert s.compile() == xml                                      # deterministic
    # the extra synth, its gain, and the limiter all made it in
    libs = [lib_of(b) for b in machine_blocks(xml)]
    assert 'Pedal FM' in libs and 'Pedal Limit' in libs
    assert any(name_of(b) == 'Lead2Gain' for b in machine_blocks(xml) if lib_of(b) == 'Pedal Gain')


def test_compose_unknown_voice():
    from rebuzz import compose
    try:
        compose({'name': 'X', 'sections': {'A': ['A']}, 'arrange': ['A'],
                 'voices': [{'type': 'glockenspiel', 'slot': 'Pad'}]}).compile()
        assert False, 'expected ValueError for unknown voice type'
    except ValueError:
        pass


def test_loop_safety_first_section_late_hit():
    # a voice active in the FIRST section but whose first strike is mid-bar must
    # still get a row-0 release on its own pattern, else it drones on the loop wrap
    s = Song('Late', bpm=90, tpb=8, key='A', scale='blues')
    s.section('V', ['A', 'A', 'D', 'E'])
    s.add(Chords('Comp', octave=3, chord='dom7', rhythm='..x...x.'))   # no row-0 hit
    s.arrange(['V'])
    xml = s.compile()                                  # compiles only if loop-safe
    assert validate(xml).ok
    got0 = False
    for b in machine_blocks(xml):
        if lib_of(b) == 'Modern Pattern Editor':
            m = re.search(r'<Data>([A-Za-z0-9+/=]+)</Data>', b)
            d = m and decode_blob(base64.b64decode(m.group(1)))
            if d and d.get('mname') == 'Comp':
                got0 = any(r == 0 and v == 255
                           for col in d['patterns']['00'].values() for r, v in col)
    assert got0


def test_lastcall_spec_round_trips():
    import json
    import importlib
    from rebuzz import compose
    spec = importlib.import_module('build_lastcall').LASTCALL_SPEC
    xml = compose(json.loads(json.dumps(spec))).compile()      # full JSON round-trip
    assert validate(xml).ok
    # both leads survive the spec, each on its own gain (guards the 'leads lost' regression)
    assert any(lib_of(b) == 'Pedal Faze-R' and name_of(b) == 'Lead' for b in machine_blocks(xml))
    assert any(lib_of(b) == 'Pedal FM' and name_of(b) == 'Lead2' for b in machine_blocks(xml))
    assert sorted(name_of(b) for b in machine_blocks(xml) if lib_of(b) == 'Pedal Gain') == \
        ['BassGain', 'CompGain', 'Lead2Gain', 'LeadGain', 'PadGain']


if __name__ == '__main__':
    import traceback
    fails = 0
    for k, fn in sorted(globals().items()):
        if k.startswith('test_'):
            try:
                fn(); print('PASS', k)
            except Exception:
                fails += 1; print('FAIL', k); traceback.print_exc()
    sys.exit(1 if fails else 0)
