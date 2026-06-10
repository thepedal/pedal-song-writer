"""rebuzz — byte-exact helpers for generating loadable ReBuzz .bmxml songs.

Reference: docs/ReBuzz_SongFormat_Notes_BMXML.md (the format spec).

A song script supplies the music + arrangement + machine choices; this package
supplies the format-correct primitives:

    blob     build_blob / build_blob_mt / build_blob_cols, note_value, NOTE_OFF
    blocks   read, machine_blocks, name_of, lib_of, find_machine, pattern_xml, set_* mutators
    control  pedal_chord_state / pedal_chord_pattern, presetter_state / clear
    song     connection/sequence XML, splice, set_tempo, set_loop_song_end,
             rename_song, clear_held_notes, write_bmxml
"""
from .blob import (
    NOTE_OFF, note_value, b64,
    build_blob, build_blob_mt, build_blob_mt_multi,
    build_blob_cols, build_blob_cols_multi,
)
from .blocks import (
    read, machine_blocks, name_of, lib_of, find_machine,
    pattern_xml, patterns_xml, set_patterns, set_data, set_track_count,
    set_position, set_name, set_editor, set_param, set_param_track,
    machine_positions, assert_no_overlap,
)
from .control import (
    pedal_chord_state, pedal_chord_pattern,
    presetter_state, presetter_clear_stored_presets,
)
from .song import (
    connection, sequence, sequence_multi, machines_xml, connections_xml,
    connections_xml_multi, sequences_xml, sequences_xml_multi,
    splice, set_loop_song_end, set_tempo, rename_song, clear_held_notes,
    write_bmxml,
)

from .validate import validate, assert_valid, ValidationError, Report, decode_blob

from .theory import Scale, parse_note, chord_code, arp_mode
from .dsl import Song, Section, Chords, Arp, Drums, Melody, compose, steps_to_rows, swing_rows, db_to_amp

__all__ = [
    'NOTE_OFF', 'note_value', 'b64',
    'build_blob', 'build_blob_mt', 'build_blob_mt_multi',
    'build_blob_cols', 'build_blob_cols_multi',
    'read', 'machine_blocks', 'name_of', 'lib_of', 'find_machine',
    'pattern_xml', 'patterns_xml', 'set_patterns', 'set_data', 'set_track_count',
    'set_position', 'set_name', 'set_editor', 'set_param', 'set_param_track',
    'machine_positions', 'assert_no_overlap',
    'validate', 'assert_valid', 'ValidationError', 'Report', 'decode_blob',
    'Scale', 'parse_note', 'chord_code', 'arp_mode',
    'Song', 'Section', 'Chords', 'Arp', 'Drums', 'Melody', 'compose', 'steps_to_rows', 'swing_rows', 'db_to_amp',
    'pedal_chord_state', 'pedal_chord_pattern',
    'presetter_state', 'presetter_clear_stored_presets',
    'connection', 'sequence', 'sequence_multi', 'machines_xml', 'connections_xml',
    'connections_xml_multi', 'sequences_xml', 'sequences_xml_multi',
    'splice', 'set_loop_song_end', 'set_tempo', 'rename_song', 'clear_held_notes',
    'write_bmxml',
]
