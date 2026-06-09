"""Reading reference songs and surgically editing `<Machine>` blocks.

The cardinal rule (BMXML §6): never fabricate a `<Machine>` block — extract a
real one from a ReBuzz-saved song and retarget it with the mutators here.
"""
import re
from .blob import b64


def read(path):
    """Read a .bmxml as text, stripping the UTF-8 BOM."""
    return open(path, 'rb').read().decode('utf-8-sig')


def machine_blocks(raw):
    """Return each top-level <Machine>...</Machine> block (nesting-aware)."""
    ms = raw.index('<Machines>')
    me = raw.index('</Machines>')
    seg = raw[ms + len('<Machines>'):me]
    out = []
    depth = 0
    start = None
    for m in re.finditer(r'</?Machine>', seg):
        if m.group(0) == '<Machine>':
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                out.append(seg[start:m.end()])
    return out


def name_of(block):
    m = re.search(r'<Name>(.*?)</Name>\s*<Patterns', block, re.S)
    return m.group(1) if m else None


def lib_of(block):
    return re.search(r'<Library>(.*?)</Library>', block).group(1)


def patterns_xml(specs):
    """A `<Patterns>` block with one entry per (name, length). Columns stay empty
    (`<Columns />`) — real events live in the editor blob; the sequence references
    these by name.
    """
    items = ['<Pattern>\r\n          <Name>%s</Name>\r\n          <Length>%d</Length>\r\n'
             '          <Columns />\r\n        </Pattern>' % (name, length)
             for name, length in specs]
    return '<Patterns>\r\n        ' + '\r\n        '.join(items) + '\r\n      </Patterns>'


def pattern_xml(name='00', length=256):
    """A single empty `<Patterns>` block (the common case)."""
    return patterns_xml([(name, length)])


def set_patterns(block, pat):
    """Replace a block's `<Patterns>...</Patterns>` with `pat`."""
    return re.sub(r'<Patterns>.*?</Patterns>', pat, block, count=1, flags=re.S)


def set_data(block, blob):
    """Set a block's `<Data>` to the base64 of a raw blob (bytes)."""
    return re.sub(r'<Data>.*?</Data>', '<Data>%s</Data>' % b64(blob),
                  block, count=1, flags=re.S)


def set_track_count(block, n):
    """Set the Track parameter group's `<TrackCount>` (polyphony)."""
    return re.sub(r'(<Type>Track</Type>.*?)<TrackCount>\d+</TrackCount>',
                  r'\g<1><TrackCount>%d</TrackCount>' % n, block, count=1, flags=re.S)


def set_position(block, x, y):
    """Set a machine's machine-view X/Y (keep inside the drawn canvas). Works for
    both `Generator` and `Effect` machines (Master is positioned by the host)."""
    return re.sub(r'(<Type>(?:Generator|Effect)</Type>\s*<X>)[^<]*(</X>\s*<Y>)[^<]*(</Y>)',
                  r'\g<1>%s\g<2>%s\g<3>' % (x, y), block, count=1)


def set_name(block, old, new):
    """Rename a machine (its `<Name>old</Name>` -> `<Name>new</Name>`)."""
    return block.replace('<Name>%s</Name>' % old, '<Name>%s</Name>' % new, 1)


def set_editor(block, editor):
    """Point a generator at its pattern editor (`<EditorMachine>`)."""
    return re.sub(r'<EditorMachine>_x0001_pe\d+</EditorMachine>',
                  '<EditorMachine>%s</EditorMachine>' % editor, block, count=1)


def set_param(block, name, value):
    """Set every per-track stored `<Value>` of the named `<Parameter>` to
    `value`. Used to neutralise an effect's per-track gain to unity (e.g.
    Pedal Gain Multi's `Amp`). Rewrites only the inner numeric values of the
    one parameter whose `<Name>` matches (leaving `<Track>` and other params
    untouched); robust to parameter field order.
    """
    def repl(m):
        seg = m.group(0)
        if re.search(r'<Name>%s</Name>' % re.escape(name), seg):
            seg = re.sub(r'(<Value>)-?\d+(</Value>)', r'\g<1>%d\g<2>' % value, seg)
        return seg
    return re.sub(r'<Parameter>.*?</Parameter>', repl, block, flags=re.S)


def set_param_track(block, name, track, value):
    """Set ONE track's stored value within the named `<Parameter>` (the others
    untouched). For per-input effect gains, e.g. pull track 2 of Pedal Gain
    Multi's `Amp` to attenuate the third input.
    """
    def repl(m):
        seg = m.group(0)
        if re.search(r'<Name>%s</Name>' % re.escape(name), seg):
            seg = re.sub(r'(<Track>%d</Track>\s*<Value>)-?\d+(</Value>)' % track,
                         r'\g<1>%d\g<2>' % value, seg, count=1)
        return seg
    return re.sub(r'<Parameter>.*?</Parameter>', repl, block, flags=re.S)


def machine_positions(xml, ignore_libs=('Modern Pattern Editor',)):
    """[(name, x, y), ...] for every *visible* machine in an assembled song.
    Editor backends (Modern Pattern Editor) sit at 0,0 by design and are skipped.
    """
    pts = []
    for b in machine_blocks(xml):
        if lib_of(b) in ignore_libs:
            continue
        m = re.search(r'<X>(-?\d+\.?\d*(?:[eE][-+]?\d+)?)</X>\s*'
                      r'<Y>(-?\d+\.?\d*(?:[eE][-+]?\d+)?)</Y>', b)
        if not m:
            continue
        nm = re.search(r'<Name>(.*?)</Name>', b)
        pts.append((nm.group(1) if nm else '?', float(m.group(1)), float(m.group(2))))
    return pts


def assert_no_overlap(xml, eps=0.05, ignore_libs=('Modern Pattern Editor',)):
    """Guard the machine-view layout: raise AssertionError if any two visible
    machines sit within `eps` of each other (so a stacked layout can never ship).
    Editor backends are excluded (they live at 0,0). Returns `xml` for chaining
    before write_bmxml. A real raise (not an `assert` statement) so `python -O`
    can't strip it.
    """
    pts = machine_positions(xml, ignore_libs)
    clashes = []
    for i in range(len(pts)):
        ni, xi, yi = pts[i]
        for j in range(i + 1, len(pts)):
            nj, xj, yj = pts[j]
            if ((xi - xj) ** 2 + (yi - yj) ** 2) ** 0.5 < eps:
                clashes.append('%s~%s @(%.3f,%.3f)' % (ni, nj, xj, yj))
    if clashes:
        raise AssertionError('machines overlap in the machine view (within %g): %s'
                             % (eps, '; '.join(clashes)))
    return xml
