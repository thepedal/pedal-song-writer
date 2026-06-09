# Machine catalog

Auto-generated from `MachineRef.bmxml` by `src/catalog_machines.py`. 35 machines.

Pattern column = (#Global params) + (index within Track params); the Input
group (Amp/Pan) is connection gain/pan, not a column. Splice any of these into
a song with `next(b for b in machine_blocks(read("refs/MachineRef.bmxml")) if lib_of(b)=="<Library>")`.

## Summary

| Library | Type | Tracks | Note col | #Global | #Track | State | Ed.cols |
|---|---|---|---|---|---|---|---|
| Master | Master | - |  | 3 | 0 | none | ? |
| Pedal Add-R | Generator | 1 | 25 | 25 | 2 | managed, empty (02 + 0) | 27 |
| Pedal Chord | Generator | 1 | 0 | 0 | 14 | managed XML state (253 bytes) | ? |
| Pedal Chorus | Effect | - |  | 6 | 0 | managed, empty (02 + 0) | 6 |
| Pedal Comp | Effect | - |  | 10 | 0 | managed, empty (02 + 0) | 10 |
| Pedal ConVerb | Effect | - |  | 4 | 0 | managed, empty (02 + 0) | 4 |
| Pedal Dly PCM41 | Effect | - |  | 8 | 0 | managed, empty (02 + 0) | 8 |
| Pedal Do Nuttin' | Effect | - |  | 1 | 0 | managed, empty (02 + 0) | 1 |
| Pedal EQ | Effect | - |  | 16 | 0 | managed, empty (02 + 0) | 16 |
| Pedal FFT | Effect | - |  | 8 | 0 | managed, empty (02 + 0) | 8 |
| Pedal FM | Generator | 1 | 42 | 42 | 2 | managed, empty (02 + 0) | 44 |
| Pedal Faze-R | Generator | 1 | 67 | 67 | 2 | managed, empty (02 + 0) | ? |
| Pedal Filter | Effect | - |  | 12 | 0 | managed, empty (02 + 0) | 12 |
| Pedal Folder | Effect | - |  | 9 | 0 | managed, empty (02 + 0) | 9 |
| Pedal Follower | Effect | - |  | 10 | 0 | managed XML state (234 bytes) | 10 |
| Pedal Gain | Effect | - |  | 3 | 0 | managed, empty (02 + 0) | 3 |
| Pedal Gain Multi | Effect | - |  | 8 | 0 | managed, empty (02 + 0) | ? |
| Pedal Gate | Effect | - |  | 9 | 0 | managed XML state (129 bytes) | 9 |
| Pedal HDist | Effect | - |  | 11 | 0 | managed, empty (02 + 0) | 11 |
| Pedal Hallverb | Effect | - |  | 8 | 0 | managed, empty (02 + 0) | 8 |
| Pedal Juno106 | Generator | 1 | 25 | 25 | 1 | managed, empty (02 + 0) | ? |
| Pedal LFmono | Effect | - |  | 3 | 0 | managed XML state (262 bytes) | 3 |
| Pedal Limit | Effect | - |  | 3 | 0 | managed, empty (02 + 0) | ? |
| Pedal MComp | Effect | - |  | 35 | 0 | managed, empty (02 + 0) | 35 |
| Pedal Plaits | Generator | 1 | 12 | 12 | 2 | managed, empty (02 + 0) | ? |
| Pedal Plate | Effect | - |  | 9 | 0 | managed, empty (02 + 0) | 9 |
| Pedal Presetter | Generator | 1 |  | 0 | 1 | managed XML state (703 bytes) | 1 |
| Pedal ReTrig | Effect | - |  | 10 | 0 | managed, empty (02 + 0) | 10 |
| Pedal Resonator | Effect | - |  | 9 | 0 | managed, empty (02 + 0) | 9 |
| Pedal S950 | Effect | - |  | 5 | 0 | managed, empty (02 + 0) | 5 |
| Pedal SH101 | Generator | 1 | 25 | 25 | 1 | managed, empty (02 + 0) | ? |
| Pedal Shaper | Effect | - |  | 8 | 0 | managed, empty (02 + 0) | 8 |
| Pedal Tracker | Generator | 1 | 20 | 20 | 7 | managed, empty (02 + 0) | 27 |
| Pedal Z-Plane | Effect | - |  | 15 | 0 | managed, empty (02 + 0) | 15 |
| Pedal invFFT | Generator | 1 | 28 | 28 | 1 | managed, empty (02 + 0) | ? |

## Per-machine detail

### Master  (`Master`, Master)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Word | Volume | 0 | 16384 | 0 |
| 1 | Word | BPM | 10 | 512 | 126 |
| 2 | Byte | TPB | 1 | 32 | 4 |

### Pedal Add-R  (`Generator`, Add-R)
Note column **25**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Volume | 0 | 127 | 100 |
| 1 | Byte | Partials | 1 | 64 | 48 |
| 2 | Byte | Inharmonic | 0 | 127 | 0 |
| 3 | Byte | Brightness | 0 | 127 | 70 |
| 4 | Byte | Damping | 0 | 127 | 0 |
| 5 | Byte | Damp Tilt | 0 | 127 | 80 |
| 6 | Byte | Drift | 0 | 127 | 0 |
| 7 | Byte | Phase | 0 | 127 | 0 |
| 8 | Byte | Attack | 0 | 127 | 4 |
| 9 | Byte | Decay | 0 | 127 | 60 |
| 10 | Byte | Sustain | 0 | 127 | 127 |
| 11 | Byte | Release | 0 | 127 | 40 |
| 12 | Byte | Glide | 0 | 127 | 0 |
| 13 | Byte | LFO Speed | 0 | 127 | 30 |
| 14 | Byte | LFO Wave | 0 | 3 | 0 |
| 15 | Byte | LFO Sync | 0 | 127 | 0 |
| 16 | Byte | Mod Pitch | 0 | 127 | 64 |
| 17 | Byte | Mod Bright | 0 | 127 | 64 |
| 18 | Byte | Mod Inharm | 0 | 127 | 64 |
| 19 | Byte | Mod Drift | 0 | 127 | 64 |
| 20 | Byte | Formant Cutoff | 0 | 127 | 64 |
| 21 | Byte | Formant Q | 0 | 127 | 30 |
| 22 | Byte | Formant Amount | 0 | 127 | 0 |
| 23 | Byte | Vel Sens | 0 | 127 | 80 |
| 24 | Byte | LFO Mode | 0 | 3 | 0 |

*Track (columns from 25)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 25 | Note | Note | 1 | 156 | 0 |
| 26 | Byte | Velocity | 0 | 127 | 127 |

### Pedal Chord  (`Generator`, PChord)
Note column **0**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Track (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Note | Note | 1 | 156 | 0 |
| 1 | Byte | Velocity | 1 | 127 | 100 |
| 2 | Byte | Chord | 0 | 50 | 0 |
| 3 | Byte | Mode | 0 | 5 | 0 |
| 4 | Word | Speed | 1 | 1024 | 2 |
| 5 | Word | Length | 0 | 16384 | 0 |
| 6 | Byte | Octaves | 1 | 4 | 1 |
| 7 | Byte | Step | 1 | 8 | 1 |
| 8 | Byte | Oct Walk | 0 | 2 | 0 |
| 9 | Byte | Swing | 0 | 100 | 0 |
| 10 | Byte | Swing On | 0 | 1 | 0 |
| 11 | Byte | Humanize | 0 | 100 | 0 |
| 12 | Byte | Hum. Vel | 0 | 100 | 0 |
| 13 | Byte | Arp Reset | 0 | 1 | 0 |

### Pedal Chorus  (`Effect`, PdlChorus)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Rate | 0 | 100 | 25 |
| 1 | Byte | Depth | 0 | 100 | 35 |
| 2 | Byte | Delay | 5 | 25 | 12 |
| 3 | Byte | Spread | 0 | 100 | 80 |
| 4 | Byte | Tone | 0 | 100 | 20 |
| 5 | Byte | Mix | 0 | 100 | 45 |

### Pedal Comp  (`Effect`, PComp)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Threshold | 0 | 60 | 18 |
| 1 | Byte | Ratio | 1 | 30 | 4 |
| 2 | Byte | Knee | 0 | 12 | 0 |
| 3 | Byte | Attack | 1 | 200 | 10 |
| 4 | Word | Release | 10 | 2000 | 100 |
| 5 | Byte | Makeup Gain | 0 | 24 | 0 |
| 6 | Byte | Auto Makeup | 0 | 1 | 0 |
| 7 | Byte | Wet/Dry | 0 | 100 | 100 |
| 8 | Byte | Lookahead | 0 | 20 | 0 |
| 9 | Byte | Detection | 0 | 1 | 0 |

### Pedal ConVerb  (`Effect`, ConVerb)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | IR Wave | 1 | 200 | 1 |
| 1 | Byte | Dry | 0 | 127 | 0 |
| 2 | Byte | Wet | 0 | 127 | 127 |
| 3 | Byte | Output | 0 | 48 | 24 |

### Pedal Dly PCM41  (`Effect`, PdlPCM41)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Time Mode | 0 | 2 | 0 |
| 1 | Word | Delay | 1 | 65534 | 250 |
| 2 | Byte | Feedback | 0 | 99 | 40 |
| 3 | Byte | Mix | 0 | 100 | 50 |
| 4 | Byte | HF Damp | 0 | 100 | 20 |
| 5 | Byte | LFO Rate | 0 | 100 | 0 |
| 6 | Byte | LFO Depth | 0 | 100 | 0 |
| 7 | Byte | Ping Pong | 0 | 1 | 0 |

### Pedal Do Nuttin'  (`Effect`, DoNut)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Switch | Bypass | 0 | 1 | 0 |

### Pedal EQ  (`Effect`, PdlEQ)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Bypass | 0 | 1 | 0 |
| 1 | Byte | LS Solo | 0 | 1 | 0 |
| 2 | Byte | LM Solo | 0 | 1 | 0 |
| 3 | Byte | HM Solo | 0 | 1 | 0 |
| 4 | Byte | HS Solo | 0 | 1 | 0 |
| 5 | Byte | LS Freq | 0 | 14 | 6 |
| 6 | Byte | LS Gain | 0 | 96 | 48 |
| 7 | Byte | LM Freq | 0 | 17 | 6 |
| 8 | Byte | LM Gain | 0 | 96 | 48 |
| 9 | Byte | LM Q | 0 | 16 | 6 |
| 10 | Byte | HM Freq | 0 | 15 | 8 |
| 11 | Byte | HM Gain | 0 | 96 | 48 |
| 12 | Byte | HM Q | 0 | 16 | 6 |
| 13 | Byte | HS Freq | 0 | 13 | 9 |
| 14 | Byte | HS Gain | 0 | 96 | 48 |
| 15 | Byte | Output | 0 | 96 | 48 |

### Pedal FFT  (`Effect`, PFFT)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Drive | 0 | 200 | 50 |
| 1 | Byte | Harmonics | 0 | 100 | 25 |
| 2 | Byte | Spec Gate | 0 | 100 | 0 |
| 3 | Byte | Wet Mix | 0 | 100 | 100 |
| 4 | Word | Level | 0 | 400 | 100 |
| 5 | Word | Bin Shift | 0 | 256 | 128 |
| 6 | Byte | FFT Size | 0 | 3 | 2 |
| 7 | Switch | Bypass | 0 | 1 | 0 |

### Pedal FM  (`Generator`, PedalFM)
Note column **42**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Algorithm | 0 | 7 | 0 |
| 1 | Byte | Output | 0 | 127 | 100 |
| 2 | Byte | Voices | 1 | 16 | 8 |
| 3 | Byte | Op1 Ratio | 0 | 127 | 7 |
| 4 | Byte | Op1 Detune | 0 | 100 | 50 |
| 5 | Byte | Op1 Level | 0 | 127 | 100 |
| 6 | Byte | Op1 Attack | 0 | 127 | 4 |
| 7 | Byte | Op1 Decay | 0 | 127 | 50 |
| 8 | Byte | Op1 Sustain | 0 | 127 | 100 |
| 9 | Byte | Op1 Release | 0 | 127 | 40 |
| 10 | Byte | Op2 Ratio | 0 | 127 | 7 |
| 11 | Byte | Op2 Detune | 0 | 100 | 50 |
| 12 | Byte | Op2 Level | 0 | 127 | 80 |
| 13 | Byte | Op2 Attack | 0 | 127 | 4 |
| 14 | Byte | Op2 Decay | 0 | 127 | 50 |
| 15 | Byte | Op2 Sustain | 0 | 127 | 100 |
| 16 | Byte | Op2 Release | 0 | 127 | 40 |
| 17 | Byte | Op3 Ratio | 0 | 127 | 15 |
| 18 | Byte | Op3 Detune | 0 | 100 | 50 |
| 19 | Byte | Op3 Level | 0 | 127 | 70 |
| 20 | Byte | Op3 Attack | 0 | 127 | 4 |
| 21 | Byte | Op3 Decay | 0 | 127 | 50 |
| 22 | Byte | Op3 Sustain | 0 | 127 | 100 |
| 23 | Byte | Op3 Release | 0 | 127 | 40 |
| 24 | Byte | Op4 Ratio | 0 | 127 | 7 |
| 25 | Byte | Op4 Detune | 0 | 100 | 50 |
| 26 | Byte | Op4 Level | 0 | 127 | 127 |
| 27 | Byte | Op4 Attack | 0 | 127 | 4 |
| 28 | Byte | Op4 Decay | 0 | 127 | 60 |
| 29 | Byte | Op4 Sustain | 0 | 127 | 110 |
| 30 | Byte | Op4 Release | 0 | 127 | 50 |
| 31 | Byte | Op1 Feedback | 0 | 127 | 0 |
| 32 | Byte | Compound Mod | 0 | 127 | 32 |
| 33 | Byte | Glide | 0 | 127 | 0 |
| 34 | Byte | LFO Rate | 0 | 127 | 60 |
| 35 | Byte | LFO Shape | 0 | 4 | 0 |
| 36 | Byte | LFO Pitch | 0 | 127 | 0 |
| 37 | Byte | LFO Mod | 0 | 127 | 0 |
| 38 | Byte | Op1 VelSens | 0 | 127 | 0 |
| 39 | Byte | Op2 VelSens | 0 | 127 | 0 |
| 40 | Byte | Op3 VelSens | 0 | 127 | 0 |
| 41 | Byte | Op4 VelSens | 0 | 127 | 0 |

*Track (columns from 42)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 42 | Note | Note | 1 | 156 | 0 |
| 43 | Byte | Velocity | 0 | 127 | 127 |

### Pedal Faze-R  (`Generator`, Faze-R)
Note column **67**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | OSC1 Wave | 0 | 9 | 1 |
| 1 | Byte | OSC1 Octave | 0 | 4 | 2 |
| 2 | Byte | OSC1 Semi | 0 | 24 | 12 |
| 3 | Byte | OSC1 Fine | 0 | 100 | 50 |
| 4 | Byte | OSC1 DCW | 0 | 127 | 0 |
| 5 | Byte | OSC1 Level | 0 | 127 | 100 |
| 6 | Byte | OSC2 Wave | 0 | 9 | 1 |
| 7 | Byte | OSC2 Octave | 0 | 4 | 2 |
| 8 | Byte | OSC2 Semi | 0 | 24 | 12 |
| 9 | Byte | OSC2 Fine | 0 | 100 | 50 |
| 10 | Byte | OSC2 DCW | 0 | 127 | 0 |
| 11 | Byte | OSC2 Level | 0 | 127 | 0 |
| 12 | Byte | Osc Mode | 0 | 2 | 0 |
| 13 | Byte | Portamento | 0 | 127 | 0 |
| 14 | Byte | DCW Attack | 0 | 127 | 0 |
| 15 | Byte | DCW Decay | 0 | 127 | 70 |
| 16 | Byte | DCW Sustain | 0 | 127 | 80 |
| 17 | Byte | DCW Release | 0 | 127 | 50 |
| 18 | Byte | DCW Env Amt | 0 | 127 | 90 |
| 19 | Byte | DCW Vel | 0 | 127 | 0 |
| 20 | Byte | Amp Attack | 0 | 127 | 0 |
| 21 | Byte | Amp Decay | 0 | 127 | 70 |
| 22 | Byte | Amp Sustain | 0 | 127 | 110 |
| 23 | Byte | Amp Release | 0 | 127 | 35 |
| 24 | Byte | Amp Vel | 0 | 127 | 70 |
| 25 | Byte | Pitch Attack | 0 | 127 | 0 |
| 26 | Byte | Pitch Decay | 0 | 127 | 40 |
| 27 | Byte | Pitch Depth | 0 | 127 | 64 |
| 28 | Byte | LFO Wave | 0 | 4 | 0 |
| 29 | Byte | LFO Rate | 0 | 127 | 50 |
| 30 | Byte | LFO Delay | 0 | 127 | 0 |
| 31 | Byte | LFO Pitch | 0 | 127 | 0 |
| 32 | Byte | LFO DCW | 0 | 127 | 0 |
| 33 | Byte | LFO Amp | 0 | 127 | 0 |
| 34 | Byte | Tone | 0 | 127 | 127 |
| 35 | Byte | Tone Track | 0 | 127 | 0 |
| 36 | Byte | Tone Res | 0 | 127 | 0 |
| 37 | Byte | Oversample | 0 | 2 | 1 |
| 38 | Byte | Volume | 0 | 127 | 100 |
| 39 | Byte | DCW Track | 0 | 127 | 64 |
| 40 | Byte | LFO Sync | 0 | 1 | 0 |
| 41 | Byte | LFO Division | 0 | 7 | 2 |
| 42 | Byte | Noise Level | 0 | 127 | 0 |
| 43 | Byte | DCW2 Env | 0 | 1 | 0 |
| 44 | Byte | DCW2 Attack | 0 | 127 | 0 |
| 45 | Byte | DCW2 Decay | 0 | 127 | 70 |
| 46 | Byte | DCW2 Sustain | 0 | 127 | 80 |
| 47 | Byte | DCW2 Release | 0 | 127 | 50 |
| 48 | Byte | DCW2 Env Amt | 0 | 127 | 90 |
| 49 | Byte | LFO2 Wave | 0 | 4 | 0 |
| 50 | Byte | LFO2 Rate | 0 | 127 | 50 |
| 51 | Byte | LFO2 Sync | 0 | 1 | 0 |
| 52 | Byte | LFO2 Division | 0 | 7 | 2 |
| 53 | Byte | LFO2 Delay | 0 | 127 | 0 |
| 54 | Byte | LFO2 Pitch | 0 | 127 | 0 |
| 55 | Byte | LFO2 DCW | 0 | 127 | 0 |
| 56 | Byte | LFO2 Amp | 0 | 127 | 0 |
| 57 | Byte | Chorus | 0 | 1 | 0 |
| 58 | Byte | Chorus Rate | 0 | 127 | 30 |
| 59 | Byte | Chorus Depth | 0 | 127 | 50 |
| 60 | Byte | Chorus Mix | 0 | 127 | 50 |
| 61 | Byte | Filter Type | 0 | 3 | 0 |
| 62 | Byte | Filter Env Amt | 0 | 127 | 64 |
| 63 | Byte | Filter Attack | 0 | 127 | 0 |
| 64 | Byte | Filter Decay | 0 | 127 | 60 |
| 65 | Byte | Filter Sustain | 0 | 127 | 80 |
| 66 | Byte | Filter Release | 0 | 127 | 40 |

*Track (columns from 67)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 67 | Note | SetNote | 1 | 156 | 0 |
| 68 | Byte | Velocity | 0 | 127 | 100 |

### Pedal Filter  (`Effect`, PdlFlt)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Mode | 0 | 4 | 0 |
| 1 | Byte | Slope | 0 | 1 | 0 |
| 2 | Word | Cutoff | 20 | 18000 | 2000 |
| 3 | Byte | Resonance | 0 | 100 | 20 |
| 4 | Byte | Drive | 0 | 100 | 0 |
| 5 | Byte | LFO Wave | 0 | 5 | 0 |
| 6 | Byte | LFO Rate | 0 | 200 | 20 |
| 7 | Byte | Tempo Sync | 0 | 1 | 0 |
| 8 | Byte | LFO Div | 0 | 13 | 4 |
| 9 | Byte | LFO Depth | 0 | 100 | 0 |
| 10 | Byte | Phase Offset | 0 | 180 | 0 |
| 11 | Byte | Mix | 0 | 100 | 100 |

### Pedal Folder  (`Effect`, PFold)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Drive | 0 | 127 | 32 |
| 1 | Byte | Fold | 0 | 127 | 64 |
| 2 | Byte | Feedback | 0 | 127 | 0 |
| 3 | Byte | Output | 0 | 127 | 64 |
| 4 | Byte | Mix | 0 | 127 | 127 |
| 5 | Byte | Bias | 0 | 127 | 64 |
| 6 | Byte | PreTilt | 0 | 127 | 64 |
| 7 | Byte | Shape | 0 | 2 | 0 |
| 8 | Byte | OS | 0 | 2 | 1 |

### Pedal Follower  (`Effect`, PFol)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Detection | 0 | 1 | 0 |
| 1 | Byte | Attack | 0 | 127 | 30 |
| 2 | Byte | Release | 0 | 127 | 70 |
| 3 | Byte | Sensitivity | 0 | 48 | 24 |
| 4 | Byte | Threshold | 0 | 60 | 60 |
| 5 | Byte | Curve | 0 | 3 | 0 |
| 6 | Byte | Out Low | 0 | 127 | 0 |
| 7 | Byte | Out High | 0 | 127 | 127 |
| 8 | Byte | Smooth | 0 | 127 | 0 |
| 9 | Byte | Bypass | 0 | 1 | 0 |

### Pedal Gain  (`Effect`, PGain)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Gain | 0 | 200 | 100 |
| 1 | Byte | Mute | 0 | 1 | 0 |
| 2 | Word | Inertia | 0 | 500 | 20 |

### Pedal Gain Multi  (`Effect`, GainMulti)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Gain | 0 | 200 | 100 |
| 1 | Switch | Solo 1 | 0 | 1 | 0 |
| 2 | Switch | Solo 2 | 0 | 1 | 0 |
| 3 | Switch | Solo 3 | 0 | 1 | 0 |
| 4 | Switch | Solo 4 | 0 | 1 | 0 |
| 5 | Switch | Solo 5 | 0 | 1 | 0 |
| 6 | Switch | Solo 6 | 0 | 1 | 0 |
| 7 | Switch | Mute | 0 | 1 | 0 |

### Pedal Gate  (`Effect`, PdlGate)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Threshold | 0 | 120 | 60 |
| 1 | Byte | Hysteresis | 0 | 20 | 6 |
| 2 | Word | Attack ms | 0 | 500 | 5 |
| 3 | Word | Hold ms | 0 | 2000 | 100 |
| 4 | Word | Release ms | 1 | 2000 | 200 |
| 5 | Byte | Range dB | 0 | 90 | 0 |
| 6 | Byte | Detection | 0 | 1 | 0 |
| 7 | Byte | Lookahead ms | 0 | 25 | 0 |
| 8 | Byte | Bypass | 0 | 1 | 0 |

### Pedal HDist  (`Effect`, HDist)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Type | 0 | 7 | 0 |
| 1 | Byte | Drive | 0 | 127 | 32 |
| 2 | Byte | Bias | 0 | 127 | 64 |
| 3 | Byte | Tone | 0 | 96 | 48 |
| 4 | Byte | Mix | 0 | 100 | 100 |
| 5 | Byte | Output | 0 | 96 | 48 |
| 6 | Byte | PreCut | 0 | 127 | 0 |
| 7 | Byte | PreMid | 0 | 96 | 48 |
| 8 | Byte | LoKeep | 0 | 127 | 0 |
| 9 | Byte | Sag | 0 | 127 | 0 |
| 10 | Byte | Oversample | 0 | 1 | 0 |

### Pedal Hallverb  (`Effect`, PedalHV)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Pre Delay | 0 | 100 | 30 |
| 1 | Word | Decay Time | 100 | 6000 | 2500 |
| 2 | Byte | Room Size | 0 | 100 | 75 |
| 3 | Byte | Damping | 0 | 100 | 35 |
| 4 | Byte | Diffusion | 0 | 100 | 75 |
| 5 | Byte | Width | 0 | 100 | 90 |
| 6 | Byte | Wet Level | 0 | 100 | 70 |
| 7 | Byte | Dry Level | 0 | 100 | 100 |

### Pedal Juno106  (`Generator`, Juno106)
Note column **25**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | LFO Rate | 0 | 127 | 64 |
| 1 | Byte | LFO Delay | 0 | 127 | 0 |
| 2 | Byte | DCO LFO | 0 | 127 | 0 |
| 3 | Byte | DCO PWM | 0 | 127 | 0 |
| 4 | Byte | DCO PWM Src | 0 | 2 | 0 |
| 5 | Byte | DCO PW | 0 | 127 | 64 |
| 6 | Byte | DCO Range | 0 | 2 | 1 |
| 7 | Switch | DCO Pulse | 0 | 1 | 0 |
| 8 | Switch | DCO Saw | 0 | 1 | 1 |
| 9 | Byte | DCO Sub | 0 | 127 | 0 |
| 10 | Byte | DCO Noise | 0 | 127 | 0 |
| 11 | Byte | HPF | 0 | 3 | 0 |
| 12 | Byte | VCF Freq | 0 | 127 | 100 |
| 13 | Byte | VCF Reso | 0 | 127 | 30 |
| 14 | Byte | VCF Env Amt | 0 | 127 | 80 |
| 15 | Byte | VCF Env Pol | 0 | 1 | 0 |
| 16 | Byte | VCF LFO | 0 | 127 | 0 |
| 17 | Byte | VCF Key Trk | 0 | 127 | 64 |
| 18 | Byte | VCA Mode | 0 | 1 | 0 |
| 19 | Byte | VCA Level | 0 | 127 | 100 |
| 20 | Byte | Env A | 0 | 127 | 5 |
| 21 | Byte | Env D | 0 | 127 | 60 |
| 22 | Byte | Env S | 0 | 127 | 80 |
| 23 | Byte | Env R | 0 | 127 | 40 |
| 24 | Byte | Chorus | 0 | 3 | 0 |

*Track (columns from 25)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 25 | Note | Note | 1 | 156 | 0 |

### Pedal LFmono  (`Effect`, LFMono)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Word | Crossover Hz | 40 | 800 | 230 |
| 1 | Byte | LF Level % | 0 | 200 | 100 |
| 2 | Byte | HF Level % | 0 | 200 | 100 |

### Pedal Limit  (`Effect`, Limit)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Threshold | 0 | 200 | 3 |
| 1 | Byte | Output Level | 0 | 200 | 3 |
| 2 | Byte | ISP | 0 | 1 | 0 |

### Pedal MComp  (`Effect`, MComp)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Listen | 0 | 4 | 0 |
| 1 | Byte | Xover L-LM | 0 | 127 | 52 |
| 2 | Byte | Xover LM-HM | 0 | 127 | 59 |
| 3 | Byte | Xover HM-H | 0 | 127 | 75 |
| 4 | Byte | Knee | 0 | 24 | 6 |
| 5 | Byte | Detection | 0 | 1 | 0 |
| 6 | Byte | L Threshold | 0 | 60 | 18 |
| 7 | Byte | L Ratio | 0 | 127 | 31 |
| 8 | Byte | L Attack | 0 | 127 | 95 |
| 9 | Byte | L Release | 0 | 127 | 89 |
| 10 | Byte | L Makeup | 0 | 24 | 0 |
| 11 | Byte | L Bypass | 0 | 1 | 0 |
| 12 | Byte | LM Threshold | 0 | 60 | 18 |
| 13 | Byte | LM Ratio | 0 | 127 | 31 |
| 14 | Byte | LM Attack | 0 | 127 | 77 |
| 15 | Byte | LM Release | 0 | 127 | 77 |
| 16 | Byte | LM Makeup | 0 | 24 | 0 |
| 17 | Byte | LM Bypass | 0 | 1 | 0 |
| 18 | Byte | HM Threshold | 0 | 60 | 18 |
| 19 | Byte | HM Ratio | 0 | 127 | 31 |
| 20 | Byte | HM Attack | 0 | 127 | 65 |
| 21 | Byte | HM Release | 0 | 127 | 65 |
| 22 | Byte | HM Makeup | 0 | 24 | 0 |
| 23 | Byte | HM Bypass | 0 | 1 | 0 |
| 24 | Byte | H Threshold | 0 | 60 | 18 |
| 25 | Byte | H Ratio | 0 | 127 | 31 |
| 26 | Byte | H Attack | 0 | 127 | 57 |
| 27 | Byte | H Release | 0 | 127 | 57 |
| 28 | Byte | H Makeup | 0 | 24 | 0 |
| 29 | Byte | H Bypass | 0 | 1 | 0 |
| 30 | Byte | Output Gain | 0 | 48 | 24 |
| 31 | Byte | Dry-Wet | 0 | 100 | 100 |
| 32 | Byte | Lookahead | 0 | 127 | 0 |
| 33 | Byte | Phase Linear | 0 | 1 | 0 |
| 34 | Byte | Spectrum View | 0 | 1 | 0 |

### Pedal Plaits  (`Generator`, Plaits)
Note column **12**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Engine | 0 | 12 | 0 |
| 1 | Byte | Frequency | 0 | 96 | 48 |
| 2 | Byte | Harmonics | 0 | 127 | 64 |
| 3 | Byte | Timbre | 0 | 127 | 64 |
| 4 | Byte | Morph | 0 | 127 | 64 |
| 5 | Byte | LPG Response | 0 | 127 | 0 |
| 6 | Byte | Decay | 0 | 127 | 32 |
| 7 | Byte | Volume | 0 | 127 | 100 |
| 8 | Byte | Vel Harmonics | 0 | 127 | 64 |
| 9 | Byte | Vel Timbre | 0 | 127 | 64 |
| 10 | Byte | Vel Morph | 0 | 127 | 64 |
| 11 | Byte | Vel Decay | 0 | 127 | 64 |

*Track (columns from 12)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 12 | Note | Note | 1 | 156 | 0 |
| 13 | Byte | Velocity | 0 | 127 | 100 |

### Pedal Plate  (`Effect`, PedalPlate)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Mix | 0 | 100 | 50 |
| 1 | Word | PreDelayMs | 0 | 500 | 0 |
| 2 | Byte | Decay | 0 | 100 | 75 |
| 3 | Byte | Damping | 0 | 100 | 50 |
| 4 | Byte | Size | 10 | 200 | 100 |
| 5 | Byte | ModRate | 0 | 100 | 20 |
| 6 | Byte | ModDepth | 0 | 100 | 30 |
| 7 | Byte | LowCut | 0 | 100 | 10 |
| 8 | Byte | Feedback | 0 | 95 | 0 |

### Pedal Presetter  (`Generator`, Presetter)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Track (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Preset | 0 | 253 | 0 |

### Pedal ReTrig  (`Effect`, ReTrig)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Word | ReTrigLength | 0 | 256 | 12 |
| 1 | Byte | Trigger | 0 | 1 | 0 |
| 2 | Byte | Retrigger Vol | 0 | 254 | 128 |
| 3 | Byte | BufferMode | 0 | 1 | 0 |
| 4 | Byte | Effect Command | 0 | 254 | 0 |
| 5 | Byte | Argument | 0 | 254 | 0 |
| 6 | Byte | Attack | 0 | 254 | 0 |
| 7 | Byte | Decay | 0 | 254 | 0 |
| 8 | Byte | Dry Volume | 0 | 254 | 0 |
| 9 | Byte | Clear | 0 | 1 | 0 |

### Pedal Resonator  (`Effect`, PResn)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Tuning | 0 | 5 | 0 |
| 1 | Byte | Root Note | 0 | 72 | 24 |
| 2 | Byte | Modes | 0 | 2 | 2 |
| 3 | Byte | Decay | 0 | 127 | 64 |
| 4 | Byte | Damping | 0 | 127 | 32 |
| 5 | Byte | Drive | 0 | 127 | 64 |
| 6 | Byte | Mix | 0 | 127 | 64 |
| 7 | Byte | Tone | 0 | 96 | 48 |
| 8 | Byte | Spread | 0 | 127 | 32 |

### Pedal S950  (`Effect`, PdlS950)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Drive | 0 | 127 | 0 |
| 1 | Byte | Sample Rate | 0 | 6 | 3 |
| 2 | Byte | Bit Depth | 0 | 2 | 0 |
| 3 | Byte | Mode | 0 | 2 | 1 |
| 4 | Byte | Mix | 0 | 100 | 100 |

### Pedal SH101  (`Generator`, SH101)
Note column **25**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Range | 0 | 2 | 1 |
| 1 | Byte | VCO Mod | 0 | 127 | 0 |
| 2 | Byte | PWM Source | 0 | 2 | 0 |
| 3 | Byte | PWM | 0 | 127 | 0 |
| 4 | Byte | Pulse Lvl | 0 | 127 | 100 |
| 5 | Byte | Saw Lvl | 0 | 127 | 0 |
| 6 | Byte | Sub Lvl | 0 | 127 | 0 |
| 7 | Byte | Noise Lvl | 0 | 127 | 0 |
| 8 | Byte | Sub Type | 0 | 2 | 0 |
| 9 | Byte | Cutoff | 0 | 127 | 90 |
| 10 | Byte | Resonance | 0 | 127 | 0 |
| 11 | Byte | Env Amt | 0 | 128 | 64 |
| 12 | Byte | VCF Mod | 0 | 127 | 0 |
| 13 | Byte | Kbd Follow | 0 | 2 | 0 |
| 14 | Byte | VCA Mode | 0 | 1 | 1 |
| 15 | Byte | Attack | 0 | 127 | 0 |
| 16 | Byte | Decay | 0 | 127 | 64 |
| 17 | Byte | Sustain | 0 | 127 | 100 |
| 18 | Byte | Release | 0 | 127 | 50 |
| 19 | Byte | LFO Rate | 0 | 127 | 64 |
| 20 | Byte | LFO Wave | 0 | 3 | 0 |
| 21 | Byte | LFO Delay | 0 | 127 | 0 |
| 22 | Byte | Glide | 0 | 127 | 0 |
| 23 | Byte | Tune | 0 | 100 | 50 |
| 24 | Byte | Volume | 0 | 127 | 96 |

*Track (columns from 25)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 25 | Note | Note | 1 | 156 | 0 |

### Pedal Shaper  (`Effect`, Shaper)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Drive | 0 | 96 | 48 |
| 1 | Byte | Shape | 0 | 4 | 0 |
| 2 | Byte | Tone | 0 | 127 | 64 |
| 3 | Byte | Bias | 0 | 127 | 64 |
| 4 | Byte | Mix | 0 | 127 | 127 |
| 5 | Byte | Output | 0 | 96 | 48 |
| 6 | Byte | Hysteresis | 0 | 127 | 0 |
| 7 | Byte | Dust | 0 | 127 | 0 |

### Pedal Tracker  (`Generator`, PdlTrk)
Note column **20**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Word | Master | 0 | 65534 | 32768 |
| 1 | Switch | Mute | 0 | 1 | 0 |
| 2 | Word | Mute Inertia | 0 | 500 | 50 |
| 3 | Switch | Mute Track 1 | 0 | 1 | 0 |
| 4 | Switch | Mute Track 2 | 0 | 1 | 0 |
| 5 | Switch | Mute Track 3 | 0 | 1 | 0 |
| 6 | Switch | Mute Track 4 | 0 | 1 | 0 |
| 7 | Switch | Mute Track 5 | 0 | 1 | 0 |
| 8 | Switch | Mute Track 6 | 0 | 1 | 0 |
| 9 | Switch | Mute Track 7 | 0 | 1 | 0 |
| 10 | Switch | Mute Track 8 | 0 | 1 | 0 |
| 11 | Switch | Mute Track 9 | 0 | 1 | 0 |
| 12 | Switch | Mute Track 10 | 0 | 1 | 0 |
| 13 | Switch | Mute Track 11 | 0 | 1 | 0 |
| 14 | Switch | Mute Track 12 | 0 | 1 | 0 |
| 15 | Switch | Mute Track 13 | 0 | 1 | 0 |
| 16 | Switch | Mute Track 14 | 0 | 1 | 0 |
| 17 | Switch | Mute Track 15 | 0 | 1 | 0 |
| 18 | Switch | Mute Track 16 | 0 | 1 | 0 |
| 19 | Byte | Interpolation | 0 | 5 | 2 |

*Track (columns from 20)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 20 | Note | Note | 1 | 156 | 0 |
| 21 | Byte | Wave | 1 | 200 | 1 |
| 22 | Byte | Volume | 0 | 254 | 128 |
| 23 | Byte | Cmd | 0 | 254 | 0 |
| 24 | Byte | Arg | 0 | 254 | 0 |
| 25 | Byte | Cmd2 | 0 | 254 | 0 |
| 26 | Byte | Arg2 | 0 | 254 | 0 |

### Pedal Z-Plane  (`Effect`, Z-Plane)

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Shape A | 0 | 7 | 1 |
| 1 | Byte | Shape B | 0 | 7 | 5 |
| 2 | Byte | Shape C | 0 | 7 | 6 |
| 3 | Byte | Shape D | 0 | 7 | 7 |
| 4 | Byte | Morph X | 0 | 127 | 64 |
| 5 | Byte | Morph Y | 0 | 127 | 64 |
| 6 | Byte | Depth | 0 | 127 | 64 |
| 7 | Byte | Output | 0 | 127 | 64 |
| 8 | Byte | Mix | 0 | 127 | 127 |
| 9 | Byte | LFO Rate | 0 | 127 | 32 |
| 10 | Byte | LFO X | 0 | 127 | 64 |
| 11 | Byte | LFO Y | 0 | 127 | 64 |
| 12 | Byte | Env Speed | 0 | 127 | 64 |
| 13 | Byte | Env X | 0 | 127 | 64 |
| 14 | Byte | Env Y | 0 | 127 | 64 |

### Pedal invFFT  (`Generator`, invFFT)
Note column **28**, 1 track(s).

*Input*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
|  | Word | Amp | 0 | 65534 | 16384 |
|  | Word | Pan | 0 | 32768 | 16384 |

*Global (columns from 0)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 0 | Byte | Volume | 0 | 127 | 64 |
| 1 | Byte | Amp Attack | 0 | 127 | 24 |
| 2 | Byte | Amp Decay | 0 | 127 | 64 |
| 3 | Byte | Amp Sustain | 0 | 127 | 100 |
| 4 | Byte | Amp Release | 0 | 127 | 48 |
| 5 | Byte | Brightness | 0 | 127 | 127 |
| 6 | Byte | Tilt | 0 | 127 | 64 |
| 7 | Byte | Balance | 0 | 127 | 64 |
| 8 | Byte | Bright Attack | 0 | 127 | 32 |
| 9 | Byte | Bright Decay | 0 | 127 | 80 |
| 10 | Byte | Bright Sustain | 0 | 127 | 0 |
| 11 | Byte | Bright Release | 0 | 127 | 48 |
| 12 | Byte | Bright Amount | 0 | 127 | 64 |
| 13 | Byte | Formant Centre | 0 | 127 | 64 |
| 14 | Byte | Formant Width | 0 | 127 | 64 |
| 15 | Byte | Formant Amount | 0 | 127 | 0 |
| 16 | Byte | Glide | 0 | 127 | 0 |
| 17 | Byte | Stretch | 0 | 127 | 64 |
| 18 | Byte | Anim Rate | 0 | 127 | 32 |
| 19 | Byte | Anim Depth | 0 | 127 | 0 |
| 20 | Byte | LFO Rate | 0 | 127 | 64 |
| 21 | Byte | LFO Shape | 0 | 127 | 0 |
| 22 | Byte | LFO Pitch | 0 | 127 | 64 |
| 23 | Byte | LFO Bright | 0 | 127 | 64 |
| 24 | Byte | LFO Stretch | 0 | 127 | 64 |
| 25 | Byte | LFO Volume | 0 | 127 | 64 |
| 26 | Byte | LFO Formant | 0 | 127 | 64 |
| 27 | Byte | LFO Anim | 0 | 127 | 64 |

*Track (columns from 28)*
| col | type | name | min | max | def |
|---|---|---|---|---|---|
| 28 | Note | Note | 1 | 156 | 0 |
