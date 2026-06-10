"""Static validation for assembled BMXML songs (catches wiring/loop bugs before
they reach ReBuzz). `validate(xml)` returns a Report; `assert_valid(xml)` raises
on any error and returns the xml for chaining (drop-in next to assert_no_overlap).

Checks (errors unless noted):
  1. dangling connection     - every Source/Destination names a real machine
  2. dangling sequence ref   - every sequenced Pattern exists in its machine
  3. span != length          - each placement's Span equals the pattern Length
  4. duplicate dest channel  - on a multi-in destination, channels must be unique
  5. held note on load (warn)- stored Track Note values must be 0 (§2.5)
  6. off-canvas (warn)       - a visible machine sits outside the machine view
  7. machine overlap         - two visible machines share a position
  8. loop drone              - a Pedal-Chord-driven target not re-triggered at tick 0
                               must carry a row-0 note-off on every track AND have its
                               chord sequenced at tick 0 with a stop, else a long
                               release drones on loop (§12.9.1)
"""
import re, struct, base64
from .blocks import machine_blocks, name_of, lib_of, machine_positions, assert_no_overlap

EDITOR_LIB = 'Modern Pattern Editor'
MULTI_IN_OK = ('Master',)            # summing destinations: duplicate channel 0 is fine


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    @property
    def ok(self):
        return not self.errors

    def __str__(self):
        if self.ok and not self.warnings:
            return 'validate: OK'
        out = []
        for e in self.errors:
            out.append('  ERROR  ' + e)
        for w in self.warnings:
            out.append('  warn   ' + w)
        head = 'validate: %d error(s), %d warning(s)' % (len(self.errors), len(self.warnings))
        return head + '\n' + '\n'.join(out)


class ValidationError(AssertionError):
    pass


# ---- low-level parsing ------------------------------------------------------

def _data_blob(block):
    m = re.search(r'<Data>([A-Za-z0-9+/=]+)</Data>', block)
    return base64.b64decode(m.group(1)) if m else None


def _cstr(buf, off):
    e = buf.index(b'\x00', off)
    return buf[off:e].decode('latin1'), e + 1


def decode_blob(blob):
    """Raw FF01 editor blob -> {mname, patterns:{name:{(track,col):[(row,val)]}}}."""
    if not blob or blob[:2] != b'\xff\x01':
        return None
    off = 2 + 4                                   # FF01 + uint32 total len
    pc = struct.unpack_from('<i', blob, off)[0]; off += 4
    mname, patterns = None, {}
    for _ in range(pc):
        pname, off = _cstr(blob, off)
        _, _, rec = struct.unpack_from('<iii', blob, off); off += 12
        ev = {}
        for _ in range(rec):
            gname, off = _cstr(blob, off); mname = mname or gname
            col, trk = struct.unpack_from('<ii', blob, off); off += 8
            off += 1                              # flag byte
            n = struct.unpack_from('<i', blob, off)[0]; off += 4
            evs = []
            for _ in range(n):
                pos, val = struct.unpack_from('<ii', blob, off); off += 8
                evs.append((pos // 240, val))
            off += 16                             # int32 x4 trailer
            ev[(trk, col)] = evs
        patterns[pname] = ev
    return {'mname': mname, 'patterns': patterns}


def _pattern_lengths(block):
    out = {}
    pm = re.search(r'<Patterns>(.*?)</Patterns>', block, re.S)
    if pm:
        for p in re.findall(r'<Pattern>(.*?)</Pattern>', pm.group(1), re.S):
            n = re.search(r'<Name>(.*?)</Name>', p)
            l = re.search(r'<Length>(\d+)</Length>', p)
            if n and l:
                out[n.group(1)] = int(l.group(1))
    return out


def _track_count(block):
    m = re.search(r'<Type>Track</Type>.*?<TrackCount>(\d+)</TrackCount>', block, re.S)
    return int(m.group(1)) if m else 0


def _machine_type(block):
    m = re.search(r'<Type>(Master|Generator|Effect)</Type>', block)
    return m.group(1) if m else None


def _pedal_chord_target(block):
    blob = _data_blob(block)
    if not blob or blob[:1] != b'\x02':
        return None
    ln = struct.unpack_from('<i', blob, 1)[0]
    body = blob[5:5 + ln].decode('utf-8-sig', 'replace')
    m = re.search(r'<TargetMachine>(.*?)</TargetMachine>', body)
    return m.group(1) if m else None


def _sequences(xml):
    """{machine_name: [(time, span, pattern), ...]}"""
    out = {}
    sec = re.search(r'<Sequences>(.*?)</Sequences>', xml, re.S)
    if not sec:
        return out
    for s in re.findall(r'<Sequence>(.*?)</Sequence>', sec.group(1), re.S):
        mn = re.search(r'<Machine>(.*?)</Machine>', s)
        if not mn:
            continue
        plc = []
        for ev in re.findall(r'<Event>(.*?)</Event>', s, re.S):
            t = re.search(r'<Time>(\d+)</Time>', ev)
            sp = re.search(r'<Span>(\d+)</Span>', ev)
            pat = re.search(r'<Pattern>(.*?)</Pattern>', ev)
            if t and pat:
                plc.append((int(t.group(1)), int(sp.group(1)) if sp else None, pat.group(1)))
        out[mn.group(1)] = plc
    return out


def _connections(xml):
    out = []
    for c in re.findall(r'<MachineConnection>(.*?)</MachineConnection>', xml, re.S):
        src = re.search(r'<Source>(.*?)</Source>', c)
        dst = re.search(r'<Destination>(.*?)</Destination>', c)
        dch = re.search(r'<DestinationChannel>(\d+)</DestinationChannel>', c)
        if src and dst:
            out.append((src.group(1), dst.group(1), int(dch.group(1)) if dch else 0))
    return out


# ---- the validator ----------------------------------------------------------

def validate(xml):
    rep = Report()
    blocks = machine_blocks(xml)
    names = {name_of(b) for b in blocks}
    by_name = {name_of(b): b for b in blocks}

    # editor blobs -> owning machine's events; managed machines -> metadata
    events = {}                                   # machine -> {pattern: {(trk,col):[(row,val)]}}
    for b in blocks:
        if lib_of(b) == EDITOR_LIB:
            try:
                d = decode_blob(_data_blob(b))
            except Exception:
                d = None                          # unparseable blob -> skip (don't crash validation)
            if d and d['mname']:
                events.setdefault(d['mname'], {}).update(d['patterns'])

    seqs = _sequences(xml)
    conns = _connections(xml)
    plens = {name_of(b): _pattern_lengths(b) for b in blocks}

    # 1. dangling connections -------------------------------------------------
    for src, dst, _ in conns:
        if src not in names:
            rep.errors.append('connection from unknown machine %r' % src)
        if dst not in names:
            rep.errors.append('connection to unknown machine %r' % dst)

    # 2/3. sequence pattern exists + span == length ---------------------------
    for mn, plc in seqs.items():
        if mn not in names:
            rep.errors.append('sequence for unknown machine %r' % mn)
            continue
        pats = plens.get(mn, {})
        for (t, span, pat) in plc:
            if pat not in pats:
                rep.errors.append('%s sequences pattern %r which is not defined' % (mn, pat))
            elif span is not None and span != pats[pat]:
                rep.errors.append('%s: placement of %r has Span %d but pattern Length %d'
                                  % (mn, pat, span, pats[pat]))

    # 4. duplicate destination channels (only on multi-channel destinations) --
    by_dst = {}
    for src, dst, ch in conns:
        by_dst.setdefault(dst, []).append((src, ch))
    for dst, lst in by_dst.items():
        if dst in MULTI_IN_OK:
            continue
        chans = [ch for _, ch in lst]
        if any(c > 0 for c in chans):             # destination uses discrete channels
            seen = set()
            for src, ch in lst:
                if ch in seen:
                    rep.errors.append('destination %s has two inputs on channel %d '
                                      '(second from %s)' % (dst, ch, src))
                seen.add(ch)

    # 5. held notes on load (warn) -------------------------------------------
    for b in blocks:
        for v in re.findall(r'<Value>(\d+)</Value>\s*</Value>\s*</Values>\s*<Type>Note</Type>', b):
            if int(v) != 0:
                rep.warnings.append('%s has a non-zero stored Note (%s) - clear_held_notes '
                                    'not applied? (it may drone on load)' % (name_of(b), v))
                break

    # 6. off-canvas (warn) + 7. overlap (error) ------------------------------
    for nm, x, y in machine_positions(xml):
        if not (-1.25 <= x <= 0.85 and -1.3 <= y <= 1.05):
            rep.warnings.append('%s is off-canvas at (%.2f, %.2f) - it plays but '
                                'will not show in the machine view' % (nm, x, y))
    try:
        assert_no_overlap(xml)
    except AssertionError as e:
        rep.errors.append('machine overlap: %s' % e)

    # 8. loop drone (§12.9.1) -------------------------------------------------
    # A control-driven target that isn't re-triggered at tick 0 must be released
    # so it doesn't drone across the loop. Two things are required (belt and
    # braces, because the chord's stop only halts new triggers -- a long release
    # on the voice already sounding rides on unless the target itself is sent a
    # note-off): (a) the target carries a row-0 note-off on every track of its
    # tick-0 pattern, and (b) its Pedal Chord is sequenced at tick 0 with a stop
    # (a row-0 note-off in col 0). Targets that re-articulate at tick 0 (a root
    # at row 0) are exempt -- they restate cleanly on the loop.
    driven, retrig, chord_stop0 = {}, {}, {}
    for b in blocks:
        if lib_of(b) != 'Pedal Chord':
            continue
        pc = name_of(b); tgt = _pedal_chord_target(b)
        if not tgt:
            continue
        driven.setdefault(tgt, []).append(pc)
        for (t, span, pat) in seqs.get(pc, []):
            if t != 0:
                continue
            col0 = events.get(pc, {}).get(pat, {}).get((0, 0), [])
            if any(r == 0 and v != 255 for r, v in col0):
                retrig[tgt] = True
            if any(r == 0 and v == 255 for r, v in col0):
                chord_stop0[tgt] = True

    for tgt, drivers in sorted(driven.items()):
        if retrig.get(tgt):
            continue                              # re-articulates cleanly on loop
        drv = '+'.join(sorted(drivers))
        tc = _track_count(by_name.get(tgt, '')) or 1
        t0 = [pat for (t, span, pat) in seqs.get(tgt, []) if t == 0]
        target_off = bool(t0) and all(
            any(r == 0 and v == 255 for r, v in
                [e for (trk, c), es in events.get(tgt, {}).get(t0[0], {}).items()
                 if trk == t for e in es])
            for t in range(tc))
        if not target_off:
            rep.errors.append('loop drone: %s (driven by %s) is not re-triggered at tick 0 and '
                              'lacks a row-0 note-off on its own pattern (§12.9.1) - a long '
                              'release will drone on loop' % (tgt, drv))
        elif not chord_stop0.get(tgt):
            rep.errors.append('loop drone: %s (driven by %s) has a tick-0 note-off but its Pedal '
                              'Chord is not sequenced at tick 0 to stop triggers (§12.9.1)' % (tgt, drv))
    return rep


def assert_valid(xml):
    """Raise ValidationError if any error; return xml unchanged for chaining."""
    rep = validate(xml)
    if not rep.ok:
        raise ValidationError(str(rep))
    return xml
