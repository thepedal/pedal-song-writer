"""Byte-exact Modern Pattern Editor (MPE) blob builders.

These reproduce ReBuzz's editor-blob format verbatim (verified against real saves
from Build 1827). A blob is `FF 01` + uint32 total length + int32 patternCount,
then per pattern: name\\0 + int32 f1(=4) + int32 f2(=4) + int32 recordCount, then
per column-record: machineName\\0 + int32 colIdx + int32 track + byte flag(0) +
int32 eventCount + events(int32 pos=row*240, int32 value) + int32x4 trailer(=4).

See ReBuzz_SongFormat_Notes_BMXML.md §4 for the full byte layout.
"""
import base64, struct

NOTE_OFF = 255  # Pedal Chord Note param: "255 (off) releases the voice"


def note_value(octave, idx):
    """Buzz note encoding: value = octave*16 + noteIdx + 1 (C-0 == 1)."""
    return octave * 16 + idx + 1


def b64(blob):
    """Base64 a raw blob for an XML <Data> element."""
    return base64.b64encode(blob).decode('ascii')


def build_blob(mname, patterns):
    """Single-track blob. `patterns` = [dict(name, ncols, notecol, events)].

    Every column 0..ncols-1 is emitted but only `notecol` carries events; the
    others are empty. `events` = [(row, value), ...]. Used for drums and any
    single-track part.
    """
    body = struct.pack('<i', len(patterns))
    for p in patterns:
        body += p['name'].encode('latin1') + b'\x00'
        body += struct.pack('<iii', 4, 4, p['ncols'])
        for c in range(p['ncols']):
            body += mname.encode('latin1') + b'\x00'
            body += struct.pack('<ii', c, 0) + b'\x00'
            evs = p['events'] if c == p['notecol'] else []
            body += struct.pack('<i', len(evs))
            for (row, val) in sorted(evs):
                body += struct.pack('<ii', row * 240, val)
            body += struct.pack('<iiii', 4, 4, 4, 4)
    total = 2 + 4 + len(body)
    return b'\xff\x01' + struct.pack('<I', total) + body


def build_blob_mt_multi(mname, track_param_cols, trackcount, patterns):
    """Multi-PATTERN, multi-track blob. `patterns` = [(patname, events), ...]
    where each `events` is keyed by (track, colIdx) -> [(row, value), ...] with
    rows RELATIVE to that pattern. patternCount = len(patterns). The sequence
    places each pattern by name at its Time (§ multi-pattern). Verified against
    real multi-pattern saves (DrumTest/ref2).
    """
    base = min(track_param_cols)
    recs = base + trackcount * len(track_param_cols)

    def rec(colidx, track, evs):
        r = (mname.encode('latin1') + b'\x00' + struct.pack('<ii', colidx, track)
             + b'\x00' + struct.pack('<i', len(evs)))
        for (row, val) in sorted(evs):
            r += struct.pack('<ii', row * 240, val)
        return r + struct.pack('<iiii', 4, 4, 4, 4)

    body = struct.pack('<i', len(patterns))
    for patname, events in patterns:
        body += patname.encode('latin1') + b'\x00' + struct.pack('<iii', 4, 4, recs)
        body += b''.join(rec(c, 0, []) for c in range(base))   # non-track cols, track 0
        for t in range(trackcount):
            for pc in track_param_cols:
                body += rec(pc, t, events.get((t, pc), []))
    return b'\xff\x01' + struct.pack('<I', 2 + 4 + len(body)) + body


def build_blob_mt(mname, patname, track_param_cols, trackcount, events):
    """Single-pattern multi-track blob (the common case). See build_blob_mt_multi.
    `events` keyed by (track, colIdx) -> [(row, value), ...]; {} = empty pattern.
    """
    return build_blob_mt_multi(mname, track_param_cols, trackcount, [(patname, events)])


def build_blob_cols_multi(mname, patterns):
    """Multi-PATTERN, single-track, multi-column blob.
    `patterns` = [(patname, ncols, colevents), ...] where colevents =
    {colIdx: [(row, value), ...]} with rows RELATIVE to that pattern.
    """
    body = struct.pack('<i', len(patterns))
    for patname, ncols, colevents in patterns:
        body += patname.encode('latin1') + b'\x00'
        body += struct.pack('<iii', 4, 4, ncols)
        for c in range(ncols):
            body += mname.encode('latin1') + b'\x00'
            body += struct.pack('<ii', c, 0) + b'\x00'
            evs = colevents.get(c, [])
            body += struct.pack('<i', len(evs))
            for (row, val) in sorted(evs):
                body += struct.pack('<ii', row * 240, val)
            body += struct.pack('<iiii', 4, 4, 4, 4)
    return b'\xff\x01' + struct.pack('<I', 2 + 4 + len(body)) + body


def build_blob_cols(mname, patname, ncols, colevents):
    """Single-pattern column blob (the common case). See build_blob_cols_multi.
    Used for the Master tempo pattern and the 14-column Pedal Chord pattern.
    """
    return build_blob_cols_multi(mname, [(patname, ncols, colevents)])
