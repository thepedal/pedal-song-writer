"""Tests for rebuzz.theory and rebuzz.dsl."""
import os, re, sys, base64, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from rebuzz import (Song, Chords, Arp, Drums, validate, decode_blob,
                    Scale, parse_note, chord_code, arp_mode, steps_to_rows, db_to_amp)
from rebuzz.blocks import machine_blocks, lib_of


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


def test_loop_safety_applied():
    ev = _editor_events(_demo().compile())
    def offs(slot):
        p = ev[slot]['00']
        return sorted(t for (t, c), es in p.items() if any(r == 0 and v == 255 for r, v in es))
    assert offs('Comp') == [0, 1, 2, 3, 4, 5]          # chorus-only -> released at tick 0
    assert offs('Bass') == [] and offs('Pad') == []    # fire a root at tick 0 -> exempt


def test_mix_trim_on_correct_channel():
    xml = _demo().compile()
    sb = [b for b in machine_blocks(xml) if re.search(r'<Name>SynthBus</Name>', b)][0]
    seg = [x for x in re.findall(r'<Parameter>.*?</Parameter>', sb, re.S) if '<Name>Amp</Name>' in x][0]
    amps = dict((int(t), int(v)) for t, v in
                re.findall(r'<Track>(\d+)</Track>\s*<Value>(\d+)</Value>', seg))
    assert amps[1] == 2914 and amps[0] == 16384        # Pad is channel 1 (Bass, Pad, Comp)


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
    # both buses feed the limiter, and the limiter feeds Master
    assert re.search(r'<Source>DrumBus</Source>\s*<Destination>Limit</Destination>', xml)
    assert re.search(r'<Source>SynthBus</Source>\s*<Destination>Limit</Destination>', xml)
    assert re.search(r'<Source>Limit</Source>\s*<Destination>Master</Destination>', xml)
    # transparent: Threshold and Output both at the -1.0 dB ceiling (value 10)
    lim = next(b for b in machine_blocks(xml) if lib_of(b) == 'Pedal Limit')
    assert lim.count('<Value>10</Value>') >= 2


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
