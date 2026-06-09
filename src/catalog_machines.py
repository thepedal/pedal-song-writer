#!/usr/bin/env python3
"""Read a reference .bmxml containing machine instances and emit a catalog
(refs/MACHINES.md): per machine, its library, type, polyphony, computed note
column, parameter tables (Input/Global/Track with ranges), state-blob signature,
and editor column count. Re-run when the machine reference is updated.

    python3 src/catalog_machines.py [refs/MachineRef.bmxml] [refs/MACHINES.md]

Column rule (verified against Plaits/SH101/invFFT/Juno106/Faze-R): a pattern
column index = (number of Global-group params) + (index within Track-group
params). The Input group (Amp/Pan) is connection gain/pan, not a pattern column.
"""
import sys, os, re, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebuzz.blocks import read, machine_blocks, name_of, lib_of
from rebuzz import decode_blob


def machine_type(b):
    m = re.search(r'<Type>(Master|Generator|Effect)</Type>', b)
    return m.group(1) if m else '?'


def groups(block):
    """-> {group_type: ([(type,name,min,max,def), ...], trackcount)}"""
    out = {}
    gsec = re.search(r'<ParameterGroups>(.*?)</ParameterGroups>', block, re.S)
    if not gsec:
        return out
    for g in re.findall(r'<ParameterGroup>(.*?)</ParameterGroup>', gsec.group(1), re.S):
        gt = re.search(r'<Type>(\w+)</Type>', g)
        gt = gt.group(1) if gt else '?'
        params = []
        psec = re.search(r'<Parameters>(.*?)</Parameters>', g, re.S)
        if psec:
            for p in re.findall(r'<Parameter>(.*?)</Parameter>', psec.group(1), re.S):
                ty = re.search(r'<Type>(\w+)</Type>', p)
                nm = re.search(r'<Name>(.*?)</Name>', p)
                mn = re.search(r'<MinValue>(-?\d+)</MinValue>', p)
                mx = re.search(r'<MaxValue>(-?\d+)</MaxValue>', p)
                dv = re.search(r'<DefValue>(-?\d+)</DefValue>', p)
                params.append((ty.group(1) if ty else '?', _unesc(nm.group(1)) if nm else '?',
                               mn.group(1) if mn else '', mx.group(1) if mx else '',
                               dv.group(1) if dv else ''))
        tc = re.search(r'<TrackCount>(\d+)</TrackCount>', g)
        out[gt] = (params, int(tc.group(1)) if tc else 0)
    return out


def _unesc(s):
    return re.sub(r'_x([0-9A-Fa-f]{4})_', lambda m: chr(int(m.group(1), 16)), s)


def state_sig(block):
    m = re.search(r'<Data>([A-Za-z0-9+/=]*)</Data>', block)
    if not m or not m.group(1):
        return 'none'
    raw = base64.b64decode(m.group(1))
    if raw[:1] == b'\x02' and len(raw) <= 6:
        return 'managed, empty (02 + 0)'
    if raw[:1] == b'\x02':
        return 'managed XML state (%d bytes)' % len(raw)
    return '%d bytes (%s...)' % (len(raw), raw[:4].hex())


def main(argv):
    src = argv[0] if argv else os.path.join(os.path.dirname(__file__), '..', 'refs', 'MachineRef.bmxml')
    dst = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(__file__), '..', 'refs', 'MACHINES.md')
    xml = read(src)
    blocks = [b for b in machine_blocks(xml) if lib_of(b) != 'Modern Pattern Editor']
    # editor column count by owning machine (decode editor blobs)
    edcols = {}
    for b in machine_blocks(xml):
        if lib_of(b) == 'Modern Pattern Editor':
            try:
                d = decode_blob(base64.b64decode(re.search(r'<Data>([A-Za-z0-9+/=]+)</Data>', b).group(1)))
                if d and d['mname']:
                    cols = {c for pat in d['patterns'].values() for (t, c) in pat}
                    edcols[d['mname']] = (max(cols) + 1) if cols else 0
            except Exception:
                pass

    summary, details = [], []
    summary.append('| Library | Type | Tracks | Note col | #Global | #Track | State | Ed.cols |')
    summary.append('|---|---|---|---|---|---|---|---|')
    for b in sorted(blocks, key=lib_of):
        lib, nm, typ = lib_of(b), name_of(b), machine_type(b)
        g = groups(b)
        glob = g.get('Global', ([], 0))[0]
        trk, tc = g.get('Track', ([], 0))
        inp = g.get('Input', ([], 0))[0]
        note_idx = next((i for i, (t, *_ ) in enumerate(trk) if t == 'Note'), None)
        note_col = (len(glob) + note_idx) if note_idx is not None else ''
        summary.append('| %s | %s | %s | %s | %d | %d | %s | %s |' % (
            lib, typ, tc or ('-' if typ != 'Generator' else 0),
            note_col, len(glob), len(trk), state_sig(b), edcols.get(nm, '?')))
        # detail block
        details.append('\n### %s  (`%s`, %s)' % (lib, typ, nm))
        if note_col != '':
            details.append('Note column **%s**, %d track(s).' % (note_col, tc))
        for label, ps, base in (('Input', inp, None), ('Global', glob, 0),
                                ('Track', trk, len(glob))):
            if not ps:
                continue
            details.append('\n*%s%s*' % (label, '' if base is None else ' (columns from %d)' % base))
            details.append('| col | type | name | min | max | def |')
            details.append('|---|---|---|---|---|---|')
            for i, (t, n, mn, mx, dv) in enumerate(ps):
                col = '' if base is None else base + i
                details.append('| %s | %s | %s | %s | %s | %s |' % (col, t, n, mn, mx, dv))

    md = ['# Machine catalog', '',
          'Auto-generated from `%s` by `src/catalog_machines.py`. %d machines.' % (
              os.path.basename(src), len(blocks)), '',
          'Pattern column = (#Global params) + (index within Track params); the Input',
          'group (Amp/Pan) is connection gain/pan, not a column. Splice any of these into',
          'a song with `next(b for b in machine_blocks(read("refs/MachineRef.bmxml")) '
          'if lib_of(b)=="<Library>")`.', '',
          '## Summary', ''] + summary + ['', '## Per-machine detail'] + details
    open(dst, 'w').write('\n'.join(md) + '\n')
    print('WROTE %s (%d machines)' % (dst, len(blocks)))
    print('\n'.join(summary))


if __name__ == '__main__':
    main(sys.argv[1:])
