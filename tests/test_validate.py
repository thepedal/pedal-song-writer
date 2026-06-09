"""Regression tests for rebuzz.validate and song build determinism.

Run:  cd rebuzz-songgen && python3 -m pytest tests/ -q
(or just `python3 tests/test_validate.py`)
"""
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from rebuzz import validate, assert_valid, ValidationError
from rebuzz.blob import build_blob_mt, b64

SONGS = [os.path.join(ROOT, 'songs', f) for f in ('LastCall.bmxml', 'Limani.bmxml')]


def _load(path):
    return open(path, 'rb').read().decode('utf-8-sig')


def _errs(xml):
    return validate(xml).errors


# --- the shipped songs are clean --------------------------------------------

def test_songs_validate_clean():
    for s in SONGS:
        rep = validate(_load(s))
        assert rep.ok, '%s should validate clean:\n%s' % (s, rep)


def test_assert_valid_passes_on_songs():
    for s in SONGS:
        assert assert_valid(_load(s)) == _load(s)


# --- every check fires on deliberately broken input -------------------------

def test_loop_drone_caught():
    xml = _load(SONGS[0])                                   # LastCall
    empty = b64(build_blob_mt('Comp', '00', [25], 6, {}))   # strip Comp's row-0 note-offs
    pe5 = re.search(r'<Machine>(?:(?!</Machine>).)*?<Name>_x0001_pe5</Name>.*?</Machine>',
                    xml, re.S).group(0)
    broken = xml.replace(pe5, re.sub(r'<Data>[A-Za-z0-9+/=]+</Data>',
                                     '<Data>%s</Data>' % empty, pe5, count=1))
    assert any('loop drone' in e and 'Comp' in e for e in _errs(broken))


def test_span_mismatch_caught():
    broken = _load(SONGS[0]).replace('<Span>256</Span>', '<Span>255</Span>', 1)
    assert any('Span' in e for e in _errs(broken))


def test_dangling_connection_caught():
    broken = _load(SONGS[0]).replace('<Source>Bass</Source>', '<Source>Nope</Source>', 1)
    assert any('unknown machine' in e for e in _errs(broken))


def test_duplicate_channel_caught():
    broken = re.sub(
        r'(<Source>Comp</Source>\s*<Destination>SynthBus</Destination>.*?<DestinationChannel>)3(</DestinationChannel>)',
        r'\g<1>2\g<2>', _load(SONGS[0]), count=1, flags=re.S)
    assert any('channel' in e for e in _errs(broken))


# --- builds are deterministic (guards against accidental output drift) ------

def test_build_determinism():
    for script, song in (('build_lastcall.py', 'LastCall.bmxml'),
                         ('build_limani.py', 'Limani.bmxml')):
        path = os.path.join(ROOT, 'songs', song)
        before = open(path, 'rb').read()
        subprocess.run([sys.executable, os.path.join(ROOT, 'src', script)],
                       check=True, capture_output=True)
        after = open(path, 'rb').read()
        assert before == after, '%s is not deterministic' % script


if __name__ == '__main__':
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    fails = 0
    for fn in fns:
        try:
            fn(); print('PASS', fn.__name__)
        except Exception:
            fails += 1; print('FAIL', fn.__name__); traceback.print_exc()
    sys.exit(1 if fails else 0)
