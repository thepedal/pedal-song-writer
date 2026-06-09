"""Control machines (BMXML §12): Type Generator, no audio connection, only their
editor -> Master, sequenced, target named in the state blob. Pedal Chord writes
notes (chords/arps); Pedal Presetter fires preset changes.
"""
import re, struct
from .blob import build_blob_cols


# ---- Pedal Chord ------------------------------------------------------------

def pedal_chord_state(target, basetrack=0):
    """Managed <Data> state naming the Pedal Chord's target generator."""
    xml = ('<?xml version="1.0" encoding="utf-8"?>\r\n<PedalChordState '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xmlns:xsd="http://www.w3.org/2001/XMLSchema">\r\n'
           '  <TargetMachine>%s</TargetMachine>\r\n  <BaseTrack>%d</BaseTrack>\r\n'
           '</PedalChordState>') % (target, basetrack)
    body = b'\xef\xbb\xbf' + xml.encode('utf-8')
    return bytes([2]) + struct.pack('<i', len(body)) + body


def pedal_chord_pattern(pcname, colevents):
    """The 14-column Pedal Chord pattern. `colevents` = {colIdx: [(row, val)]}.
    col 0 = root Note, 2 = chord type, 3 = mode, 4 = speed, 6 = octaves,
    13 = arp reset. Note-off in col 0 = blob.NOTE_OFF.
    """
    return build_blob_cols(pcname, '00', 14, colevents)


# ---- Pedal Presetter --------------------------------------------------------

def presetter_state(targets, max_tracks=16):
    """Managed <Data> state. `<Targets>` is ALWAYS `max_tracks` entries,
    track-indexed (machine name where assigned, xsi:nil where not).
    """
    t = (list(targets) + [None] * max_tracks)[:max_tracks]
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<PresetterState xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
             'xmlns:xsd="http://www.w3.org/2001/XMLSchema">', '  <Targets>']
    for nm in t:
        lines.append('    <string>%s</string>' % nm if nm is not None
                     else '    <string xsi:nil="true" />')
    lines += ['  </Targets>', '</PresetterState>']
    body = b'\xef\xbb\xbf' + '\r\n'.join(lines).encode('utf-8')
    return bytes([2]) + struct.pack('<i', len(body)) + body


def presetter_clear_stored_presets(block, ntracks):
    """Neutralise load-time firing: set each track's stored Preset to NoValue 255
    so only the sequenced pattern events fire.
    """
    new_vals = '<Values>\r\n' + ''.join(
        '                <Value>\r\n                  <Track>%d</Track>\r\n'
        '                  <Value>255</Value>\r\n                </Value>\r\n' % t
        for t in range(ntracks)) + '              </Values>'
    return re.sub(r'<Values>.*?</Values>(\s*<Type>Byte</Type>\s*<Name>Preset</Name>)',
                  new_vals + r'\1', block, count=1, flags=re.S)
