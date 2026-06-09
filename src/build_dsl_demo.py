#!/usr/bin/env python3
"""DSL demo: a short A-blues authored entirely through rebuzz.dsl -- no row math.
Shows sections with roots, an arp bass, block-chord pad, comped Juno stabs, a
swung lead that only plays the choruses, a Plaits kit (one drum keyed per-section),
a mix trim on the loud pad, and staggered presets. Compiles to a validated .bmxml.
"""
import os
from rebuzz.dsl import Song, Chords, Arp, Drums

s = Song('DslDemo', bpm=90, tpb=8, key='A', scale='blues')

# --- form: roots are scale-rooted note names, one per bar ---
s.section('Intro',  ['A', 'A', 'D', 'E'])
s.section('Verse',  ['A', 'A', 'D', 'E'])
s.section('Chorus', ['D', 'D', 'A', 'E'])

# --- voices (each binds to a synth slot: Bass=SH101, Pad=invFFT, Comp=Juno, Lead=Faze-R) ---
s.add(Arp('Bass', octave=2, chord='dom7', mode='up', speed=8, octaves=2))
s.add(Chords('Pad', octave=4, chord='dom7'))                                   # block, every bar
s.add(Chords('Comp', octave=3, chord='dom7', rhythm='x...x...x...x...',         # 4 stabs/bar
             sections=['Verse', 'Chorus']))
s.add(Arp('Lead', octave=5, chord='dom7', mode='updown', speed=4, octaves=2,    # choruses only
          swing=50, sections=['Chorus']))

# --- drums (one bar per step-string, tiled; Kick keyed per section) ---
s.add(Drums({
    'Kick':      {'Verse': 'x.......x.......', 'Chorus': 'x.......x.......'},    # silent in intro
    'Snare':     '....x.......x...',
    'HatClosed': 'xxxxxxxx',
    'HatOpen':   '.......x',
}))

s.arrange(['Intro', 'Verse', 'Chorus', 'Verse', 'Chorus'])
s.mix(Pad=-15)                                                                  # pad was swamping
s.presets(Pad=46, Lead=44, Comp=28)

OUT = os.environ.get('REBUZZ_OUT') or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'songs', 'DslDemo.bmxml')
n = s.write(OUT)
print('WROTE %s bytes=%d' % (OUT, n))
