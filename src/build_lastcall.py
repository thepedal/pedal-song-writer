#!/usr/bin/env python3
"""Build "Last Call" — A-blues, 90 BPM, 8 TPB — authored through the DSL.

This is the DSL rewrite of the song that build_lastcall_lowlevel.py builds by
hand (the low-level script is kept as the byte-exact reference the DSL was
generalised from). Same key / tempo / form and the same instrument roles —
SH101 boogie bass, invFFT pad, Juno106 EP stabs, a Faze-R lead that only lifts
the choruses + bridge, and a Plaits kit — but expressed as a compact score:
sections + voices + arrangement + mix + presets + a master limiter. The
compiler applies the loop-safety and §12.9 entry note-off rules and runs full
validation before writing.

One honest simplification vs the low-level build: the grooves are per-section
step-strings rather than the hand-tuned intro/fill/outro figures (no per-bar
fills yet). The shuffle feel is back, though — the kit swings its off-beat
eighths (swing=67), which reproduces the low-level version's hand-placed hat
rows exactly. Everything else carries over — the parts, the -28 dB pad trim
from the stem analysis (the pad clips at source), the one-preset-per-row
stagger, and the -1 dBFS true-peak limiter.
"""
import os
from rebuzz.dsl import Song, Chords, Arp, Drums, Melody

OUT = os.environ.get("REBUZZ_OUT") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "songs", "LastCall.bmxml")

s = Song('LastCall', bpm=90, tpb=8, key='A', scale='blues')

# Sections — roots as note names (A / D / E, with a B lift in the bridge).
s.section('Intro',  ['A', 'A', 'D', 'E'])
s.section('Verse',  ['A', 'A', 'D', 'D', 'A', 'E', 'A', 'E'])
s.section('Chorus', ['D', 'D', 'A', 'A', 'E', 'D', 'A', 'E'])
s.section('Mid8',   ['D', 'D', 'A', 'A', 'B', 'B', 'E', 'E'])
s.section('Outro',  ['A', 'D', 'A', 'A'])

# Voices — all dominant-7 colour (it's a blues).
s.add(Arp('Bass', octave=2, chord='dom7', mode='up', speed=8, octaves=1))   # walking boogie
s.add(Chords('Pad', octave=4, chord='dom7'))                                # one held chord per bar
s.add(Chords('Comp', octave=3, chord='dom7', rhythm={                       # EP stabs, per-section figure
    'Verse':  '..x...x.',     # sparse off-beat
    'Chorus': 'x.x.x.x.',     # driving
    'Mid8':   'x.......',
    'Outro':  'x.......'}))
s.add(Arp('Lead', octave=5, chord='dom7', mode='updown', speed=4, octaves=2,
          swing=50, sections=['Chorus', 'Mid8']))                           # lead only in choruses + bridge

# Plaits kit — per-section grooves (8 steps/bar = eighths), triplet shuffle.
s.add(Drums({
    'Kick':      {'Intro': 'x...x...', 'Verse': 'x...x...', 'Chorus': 'x...x..x',
                  'Mid8': 'x...x...', 'Outro': 'x...x...'},
    'Snare':     {'Verse': '..x...x.', 'Chorus': '..x...x.', 'Mid8': '..x...x.',
                  'Outro': '..x...x.'},                                       # backbeat (silent in intro)
    'HatClosed': {'Intro': 'x.x.x.x.', 'Verse': 'xxxxxxxx', 'Chorus': 'xxxxxxxx',
                  'Mid8': 'xxxxxxxx', 'Outro': 'xxxxxxxx'},
    'HatOpen':   {'Chorus': '.......x', 'Mid8': '.......x'},                  # end-of-bar open accent
}, swing=67))                                    # shuffle the off-beat eighths (matches the hand build)

s.arrange(['Intro', 'Verse', 'Chorus', 'Verse', 'Mid8', 'Chorus', 'Outro'])

# Lead2 — a real melodic line played straight into a Pedal FM (note col 42),
# spliced from MachineRef and routed to the SynthBus. It carries the verses
# (where the arp lead rests), climbs into the bridge for a two-lead climax, and
# resolves in the outro -- sitting out the choruses so it never crowds the arp.
# A blues palette (A C D Eb E G) with chord-tone colour (F# over D7, G# over E7,
# B in the bridge) and the b3/b5 blue notes up high. step/length are 16th notes.
s.synth('Lead2', 'Pedal FM', note_col=42, tracks=1)
s.add(Melody('Lead2', octave=5, grid=16, phrases={
    'Intro': [(56, 'E5', 2), (58, 'G5', 2), (60, 'A5', 4)],            # bar-4 pickup into the verse
    'Verse': [(4, 'E5', 2), (6, 'G5', 2), (8, 'A5', 4),               # bar1  E-G up to the root
              (16, 'A5', 2), (18, 'C6', 2), (20, 'A5', 2), (22, 'G5', 4),
              (32, 'F#5', 2), (36, 'A5', 2), (38, 'F#5', 2), (40, 'D5', 4),
              (48, 'E5', 2), (50, 'D5', 2), (54, 'F#5', 4),
              (68, 'A5', 2), (70, 'C6', 2), (72, 'A5', 4),            # bar5  restate, higher
              (80, 'B5', 2), (84, 'G#5', 2), (86, 'E5', 4),          # over E7
              (100, 'E5', 2), (102, 'G5', 2), (104, 'A5', 4),
              (112, 'G5', 2), (114, 'E5', 2), (116, 'D5', 2), (120, 'E5', 4)],   # turnaround
    'Mid8':  [(0, 'D6', 2), (2, 'C6', 2), (4, 'A5', 2), (6, 'C6', 2), (8, 'D6', 4),  # high entry
              (16, 'C6', 2), (18, 'A5', 2), (20, 'F#5', 2), (22, 'A5', 4),
              (32, 'E5', 2), (34, 'G5', 2), (36, 'A5', 2), (38, 'C6', 2), (40, 'Eb6', 2), (42, 'C6', 4),
              (48, 'C6', 2), (50, 'A5', 2), (52, 'G5', 2), (54, 'E5', 4),
              (64, 'F#6', 2), (66, 'E6', 2), (68, 'D6', 2), (70, 'B5', 4),      # over B, the lift
              (80, 'B5', 2), (82, 'D6', 2), (84, 'F#6', 2), (86, 'E6', 4),      # peak
              (96, 'E6', 2), (98, 'D6', 2), (100, 'B5', 2), (102, 'G5', 4),
              (112, 'G5', 2), (114, 'Eb5', 2), (116, 'E5', 2), (120, 'A5', 4)],  # wind down to A
    'Outro': [(4, 'E5', 2), (6, 'G5', 2), (8, 'A5', 4),
              (16, 'F#5', 2), (18, 'E5', 2), (20, 'D5', 4),
              (32, 'C6', 2), (34, 'A5', 2), (36, 'G5', 2), (38, 'E5', 4),
              (48, 'A5', 10)],                                          # final A, ring out
}))

s.mix(Pad=-28)                                  # pad bus trim from the stem analysis
s.presets(Bass=0, Pad=41, Lead=44, Comp=28, Lead2=15)   # +Lead2: FM 'Lead Bright'
s.limiter(ceiling=-1.0, isp=True)               # transparent true-peak safety ceiling

n = s.write(OUT)
print('WROTE %s bytes=%d' % (OUT, n))
