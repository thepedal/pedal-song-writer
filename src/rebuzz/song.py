"""Assembling a song: emit connection/sequence XML, splice machines into a real
skeleton song, set tempo/length, clear load-time held notes, and write the file
with the BOM. See BMXML §6 (assembly) and §8 (tempo).
"""
import re, os


def connection(src, dst='Master', amp=16384, pan=16384, src_ch=0, dst_ch=0):
    """A `<MachineConnection>` from `src` to `dst`. Defaults make the common
    case (audio/editor -> Master, channel 0, unity amp). For a multi-input
    effect, give each source the same `dst` with an incrementing `dst_ch`
    (0,1,2,3...); the per-input gain is `amp` (16384 = unity). Verified against
    a real Pedal Gain Multi save (§15).
    """
    return ('    <MachineConnection>\r\n      <Source>%s</Source>\r\n'
            '      <Destination>%s</Destination>\r\n      <Amp>%d</Amp>\r\n'
            '      <Pan>%d</Pan>\r\n      <SourceChannel>%d</SourceChannel>\r\n'
            '      <DestinationChannel>%d</DestinationChannel>\r\n'
            '    </MachineConnection>') % (src, dst, amp, pan, src_ch, dst_ch)


def sequence_multi(machine, placements):
    """A `<Sequence>` on `machine` placing patterns along the timeline.
    `placements` = [(time, span, pattern), ...] — `time` = absolute start row,
    `span` = pattern length (rows), `pattern` = name. Repeat a name at several
    times to tile/reuse it.
    """
    evs = ['<Event>\r\n          <Time>%d</Time>\r\n          <Type>PlayPattern</Type>\r\n'
           '          <Span>%d</Span>\r\n          <Pattern>%s</Pattern>\r\n        </Event>'
           % (time, span, pattern) for time, span, pattern in placements]
    return ('    <Sequence>\r\n      <Events>\r\n        ' + '\r\n        '.join(evs)
            + '\r\n      </Events>\r\n      <Machine>%s</Machine>\r\n'
            '      <IsDisabled>false</IsDisabled>\r\n    </Sequence>') % machine


def sequence(machine, span=256, pattern='00'):
    """A `<Sequence>` playing one pattern for `span` rows from time 0."""
    return sequence_multi(machine, [(0, span, pattern)])


def machines_xml(blocks):
    return '<Machines>\r\n    ' + '\r\n    '.join(blocks) + '\r\n  </Machines>'


def connections_xml_multi(conns):
    """`conns` = list of either `'src'` (str -> Master, defaults) or a tuple/dict
    of `connection(...)` args, e.g. ('Kick','DrumBus',16384,16384,0,0).
    """
    parts = []
    for c in conns:
        if isinstance(c, str):
            parts.append(connection(c))
        elif isinstance(c, dict):
            parts.append(connection(**c))
        else:
            parts.append(connection(*c))
    return '<MachineConnections>\r\n' + '\r\n'.join(parts) + '\r\n  </MachineConnections>'


def connections_xml(sources):
    return connections_xml_multi(list(sources))


def sequences_xml_multi(seqs):
    """`seqs` = [(machine, placements), ...] where placements is as for
    sequence_multi. One `<Sequence>` per machine.
    """
    return ('<Sequences>\r\n' + '\r\n'.join(sequence_multi(m, pl) for m, pl in seqs)
            + '\r\n  </Sequences>')


def sequences_xml(machines, span=256, pattern='00'):
    return sequences_xml_multi([(m, [(0, span, pattern)]) for m in machines])


def splice(skeleton, machines, connections, sequences):
    """Replace the skeleton song's Machines / MachineConnections / Sequences
    blocks with the supplied XML strings.
    """
    out = skeleton
    out = re.sub(r'<Machines>.*?</Machines>', lambda m: machines, out, count=1, flags=re.S)
    out = re.sub(r'<MachineConnections>.*?</MachineConnections>',
                 lambda m: connections, out, count=1, flags=re.S)
    out = re.sub(r'<Sequences>.*?</Sequences>', lambda m: sequences, out, count=1, flags=re.S)
    return out


def set_loop_song_end(xml, total, old=16):
    """Set `<LoopEnd>` and `<SongEnd>` from the skeleton's `old` to `total` rows."""
    xml = xml.replace('<LoopEnd>%d</LoopEnd>' % old, '<LoopEnd>%d</LoopEnd>' % total)
    xml = xml.replace('<SongEnd>%d</SongEnd>' % old, '<SongEnd>%d</SongEnd>' % total)
    return xml


def set_tempo(xml, bpm, tpb):
    """Set the Master generator's stored BPM/TPB params (the actual driving tempo
    is the Master editor pattern, §8 — set that separately via build_blob_cols).
    """
    xml = re.sub(r'<Value>\d+</Value>(\s*</Value>\s*</Values>\s*<Type>Word</Type>\s*<Name>BPM</Name>)',
                 '<Value>%d</Value>' % bpm + r'\1', xml, count=1)
    xml = re.sub(r'<Value>\d+</Value>(\s*</Value>\s*</Values>\s*<Type>Byte</Type>\s*<Name>TPB</Name>)',
                 '<Value>%d</Value>' % tpb + r'\1', xml, count=1)
    return xml


def rename_song(xml, old, new):
    """Set the `<ReBuzzSong ... Name="...">` attribute."""
    return re.sub(r'(<ReBuzzSong[^>]*?)Name="%s"' % re.escape(old),
                  r'\1Name="%s"' % new, xml, count=1)


def clear_held_notes(xml):
    """Zero every Track-group Note stored value so nothing drones on load (§2.5).
    Playback notes come from the editor blobs, not these stored values.
    """
    return re.sub(r'<Value>\d+</Value>(\s*</Value>\s*</Values>\s*<Type>Note</Type>)',
                  r'<Value>0</Value>\1', xml)


def write_bmxml(path, xml):
    """Write the song with the required UTF-8 BOM. Returns the byte count."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    data = b'\xef\xbb\xbf' + xml.encode('utf-8')
    open(path, 'wb').write(data)
    return len(data)
