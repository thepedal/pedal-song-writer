#!/usr/bin/env python3
"""Build "Last Call" — A-blues, 90 BPM, 8 TPB — from a single declarative spec.

The whole song is the LASTCALL_SPEC dict below: sections, voices (SH101 boogie
bass, invFFT pad, Juno106 EP stabs, a Faze-R lead that lifts only the choruses +
bridge, a Plaits shuffle kit, and a real FM melodic lead), the arrangement, the
mix, the presets, and a master limiter. One compose() call turns it into a
validated, loadable .bmxml — the 'spec -> song' goal (BMXML §13, §21) on a real,
complete arrangement. The spec is plain JSON-serialisable data (round-tripped
through json here to prove it), so a song can be stored, diffed, or generated.

build_lastcall_lowlevel.py remains the hand-built byte-exact reference the DSL
was generalised from. The grooves here are per-section step-strings (no per-bar
fills yet); the kit swings its off-beat eighths (swing=67), reproducing the hand
build's hat rows. The -28 dB pad trim comes from the stem analysis (the pad
clips at source); presets stagger one per row; the limiter is a -1 dBFS
true-peak safety ceiling.
"""
import os
import json
from rebuzz import compose

OUT = os.environ.get("REBUZZ_OUT") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "songs", "LastCall.bmxml")

LASTCALL_SPEC = {
    'name': 'LastCall', 'bpm': 90, 'tpb': 8, 'key': 'A', 'scale': 'blues',

    # Sections — roots as note names (A / D / E, with a B lift in the bridge).
    'sections': {
        'Intro':  ['A', 'A', 'D', 'E'],
        'Verse':  ['A', 'A', 'D', 'D', 'A', 'E', 'A', 'E'],
        'Chorus': ['D', 'D', 'A', 'A', 'E', 'D', 'A', 'E'],
        'Mid8':   ['D', 'D', 'A', 'A', 'B', 'B', 'E', 'E'],
        'Outro':  ['A', 'D', 'A', 'A'],
    },

    # Lead2 — an extra synth (Pedal FM, note col 42) spliced in to host the melody.
    'synths': [{'name': 'Lead2', 'library': 'Pedal FM', 'note_col': 42, 'tracks': 1}],

    # Voices — all dominant-7 colour (it's a blues). Listed in the order they sum:
    # bass, pad, comp, lead, then drums and the melodic lead.
    'voices': [
        {'type': 'arp', 'slot': 'Bass', 'octave': 2, 'chord': 'dom7',
         'mode': 'up', 'speed': 8, 'octaves': 1},                         # walking boogie
        {'type': 'chords', 'slot': 'Pad', 'octave': 4, 'chord': 'dom7'},  # one held chord per bar
        {'type': 'chords', 'slot': 'Comp', 'octave': 3, 'chord': 'dom7',  # EP stabs, per-section figure
         'rhythm': {'Verse': '..x...x.', 'Chorus': 'x.x.x.x.',
                    'Mid8': 'x.......', 'Outro': 'x.......'}},
        {'type': 'arp', 'slot': 'Lead', 'octave': 5, 'chord': 'dom7',     # lead lifts choruses + bridge
         'mode': 'updown', 'speed': 4, 'octaves': 2, 'swing': 50,
         'sections': ['Chorus', 'Mid8']},
        {'type': 'drums', 'swing': 67, 'patterns': {                      # Plaits kit, triplet shuffle
            'Kick':      {'Intro': 'x...x...', 'Verse': 'x...x...', 'Chorus': 'x...x..x',
                          'Mid8': 'x...x...', 'Outro': 'x...x...'},
            'Snare':     {'Verse': '..x...x.', 'Chorus': '..x...x.', 'Mid8': '..x...x.',
                          'Outro': '..x...x.'},
            'HatClosed': {'Intro': 'x.x.x.x.', 'Verse': 'xxxxxxxx', 'Chorus': 'xxxxxxxx',
                          'Mid8': 'xxxxxxxx', 'Outro': 'xxxxxxxx'},
            'HatOpen':   {'Chorus': '.......x', 'Mid8': '.......x'},
        }},
        # Lead2 — a real melodic line straight into the FM (no Pedal Chord). A-blues
        # palette with chord-tone colour; carries the verses, climbs the bridge,
        # resolves in the outro, sits out the choruses. step/length are 16th notes.
        {'type': 'melody', 'slot': 'Lead2', 'octave': 5, 'grid': 16, 'phrases': {
            'Intro': [[56, 'E5', 2], [58, 'G5', 2], [60, 'A5', 4]],
            'Verse': [[4, 'E5', 2], [6, 'G5', 2], [8, 'A5', 4],
                      [16, 'A5', 2], [18, 'C6', 2], [20, 'A5', 2], [22, 'G5', 4],
                      [32, 'F#5', 2], [36, 'A5', 2], [38, 'F#5', 2], [40, 'D5', 4],
                      [48, 'E5', 2], [50, 'D5', 2], [54, 'F#5', 4],
                      [68, 'A5', 2], [70, 'C6', 2], [72, 'A5', 4],
                      [80, 'B5', 2], [84, 'G#5', 2], [86, 'E5', 4],
                      [100, 'E5', 2], [102, 'G5', 2], [104, 'A5', 4],
                      [112, 'G5', 2], [114, 'E5', 2], [116, 'D5', 2], [120, 'E5', 4]],
            'Mid8':  [[0, 'D6', 2], [2, 'C6', 2], [4, 'A5', 2], [6, 'C6', 2], [8, 'D6', 4],
                      [16, 'C6', 2], [18, 'A5', 2], [20, 'F#5', 2], [22, 'A5', 4],
                      [32, 'E5', 2], [34, 'G5', 2], [36, 'A5', 2], [38, 'C6', 2], [40, 'Eb6', 2], [42, 'C6', 4],
                      [48, 'C6', 2], [50, 'A5', 2], [52, 'G5', 2], [54, 'E5', 4],
                      [64, 'F#6', 2], [66, 'E6', 2], [68, 'D6', 2], [70, 'B5', 4],
                      [80, 'B5', 2], [82, 'D6', 2], [84, 'F#6', 2], [86, 'E6', 4],
                      [96, 'E6', 2], [98, 'D6', 2], [100, 'B5', 2], [102, 'G5', 4],
                      [112, 'G5', 2], [114, 'Eb5', 2], [116, 'E5', 2], [120, 'A5', 4]],
            'Outro': [[4, 'E5', 2], [6, 'G5', 2], [8, 'A5', 4],
                      [16, 'F#5', 2], [18, 'E5', 2], [20, 'D5', 4],
                      [32, 'C6', 2], [34, 'A5', 2], [36, 'G5', 2], [38, 'E5', 4],
                      [48, 'A5', 10]],
        }},
    ],

    'arrange': ['Intro', 'Verse', 'Chorus', 'Verse', 'Mid8', 'Chorus', 'Outro'],

    # Per-synth effects, inserted between each synth and its gain (Bass stays dry
    # to keep the low end tight). Different effect per instrument, by role:
    #   Pad   -> Chorus   : slow wide ensemble drift thickens the sustained bed
    #   Comp  -> Plate    : short, bright plate ambience/tail on the EP stabs
    #   Lead  -> Hallverb : a medium hall glues the busy arp + adds air (no extra
    #                       note clutter, which a delay would add to a busy part)
    #   Lead2 -> Delay    : a ~130 ms slapback fills space around the sparse, singing
    #                       FM lead -- the bluesy echo idiom, low feedback (1-2 taps)
    'fx': {
        'Pad':   {'library': 'Pedal Chorus',
                  'params': {'Rate': 18, 'Depth': 40, 'Spread': 90, 'Mix': 40}},
        'Comp':  {'library': 'Pedal Plate',
                  'params': {'Mix': 22, 'PreDelayMs': 10, 'Decay': 45,
                             'Damping': 55, 'Size': 80, 'LowCut': 15}},
        'Lead':  {'library': 'Pedal Hallverb',
                  'params': {'Pre Delay': 25, 'Decay Time': 1800, 'Room Size': 70,
                             'Damping': 45, 'Wet Level': 35}},
        'Lead2': {'library': 'Pedal Dly PCM41',
                  'params': {'Time Mode': 0, 'Delay': 130, 'Feedback': 18,
                             'Mix': 24, 'HF Damp': 35}},
    },
    'mix': {'Pad': -28},
    'presets': {'Bass': 0, 'Pad': 41, 'Lead': 44, 'Comp': 28, 'Lead2': 15},
    'limiter': {'ceiling': -1.0, 'isp': True},
}

if __name__ == '__main__':
    spec = json.loads(json.dumps(LASTCALL_SPEC))           # prove it's plain JSON data
    n = compose(spec).write(OUT)
    print('WROTE %s bytes=%d' % (OUT, n))
