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

Two honest simplifications vs the low-level build: the kit is straight-feel
(the DSL has no per-hit swing or per-bar fills), and the grooves are
per-section step-strings rather than the hand-tuned intro/fill/outro figures.
Everything else carries over — the parts, the -28 dB pad trim from the stem
analysis (the pad clips at source), the one-preset-per-row stagger, and the
-1 dBFS true-peak limiter, now folded into the DSL.
"""
import os
from rebuzz.dsl import Song, Chords, Arp, Drums

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

# Straight-feel Plaits kit — per-section grooves (8 steps/bar = eighths).
s.add(Drums({
    'Kick':      {'Intro': 'x...x...', 'Verse': 'x...x...', 'Chorus': 'x...x..x',
                  'Mid8': 'x...x...', 'Outro': 'x...x...'},
    'Snare':     {'Verse': '..x...x.', 'Chorus': '..x...x.', 'Mid8': '..x...x.',
                  'Outro': '..x...x.'},                                       # backbeat (silent in intro)
    'HatClosed': {'Intro': 'x.x.x.x.', 'Verse': 'xxxxxxxx', 'Chorus': 'xxxxxxxx',
                  'Mid8': 'xxxxxxxx', 'Outro': 'xxxxxxxx'},
    'HatOpen':   {'Chorus': '.......x', 'Mid8': '.......x'},                  # end-of-bar open accent
}))

s.arrange(['Intro', 'Verse', 'Chorus', 'Verse', 'Mid8', 'Chorus', 'Outro'])
s.mix(Pad=-28)                                  # pad bus trim from the stem analysis
s.presets(Bass=0, Pad=41, Lead=44, Comp=28)     # Acid Bass / Pad-Dark / Faze-R / Juno EP
s.limiter(ceiling=-1.0, isp=True)               # transparent true-peak safety ceiling

n = s.write(OUT)
print('WROTE %s bytes=%d' % (OUT, n))
