# rebuzz-songgen

Programmatic generation of **loadable ReBuzz `.bmxml` song files** from Python.

ReBuzz stores playable notes not in the visible pattern XML but in base64-encoded
*Modern Pattern Editor* blobs, with a handful of byte-exact structural rules that
must all be right or the song fails to load (or loads silent). This repo encodes
those rules in a working generator and documents them in full, so new songs can
be built from a spec — *"a ~1-minute piece in style X, instruments Y/Z, tempo
T"* — rather than hand-edited.

Two worked examples ship in `songs/`:

- **"Limani"** — D-Hijaz, 60 BPM, ~64 s, 28 machines (a 4-piece drum kit played
  directly, four synths each driven by a Pedal Chord control machine, a Pedal
  Presetter setting timbres). One pattern per machine — the simplest shape.
- **"Last Call"** — swung A-blues, 90 BPM, ~2:08, with the drums and the synths
  each routed through their own **Pedal Gain Multi submix bus** (§15). The drums
  and Pedal Chords carry **one named pattern per section** (Intro / Verse /
  Chorus / Mid8 / Outro) placed on the timeline, with Verse and Chorus reused at
  both occurrences — the navigable, multi-pattern shape (§14).

## Layout

```
rebuzz-songgen/
├── README.md
├── docs/
│   └── ReBuzz_SongFormat_Notes_BMXML.md   # the format spec — read this first
├── refs/                                  # REAL ReBuzz-saved songs (see refs/README.md)
│   ├── README.md                          #   provenance + role of each file
│   ├── synthref.bmxml                     #   [build] skeleton + 4 synth blocks
│   ├── DrumTest.bmxml                     #   [build] 4 Pedal Plaits drum blocks
│   ├── chordref.bmxml                     #   [build] Pedal Chord + pattern-editor template
│   ├── presetter_ref.bmxml               #   [build] Pedal Presetter template
│   ├── gainref.bmxml                      #   [build] Pedal Gain Multi multi-in effect (§15)
│   ├── arpref.bmxml                       #   [ref]   Pedal Chord arp-mode params (§12)
│   ├── MasterRef.bmxml                    #   [ref]   Master-track tempo layout (§8)
│   └── tracks6.bmxml                      #   [ref]   6-track multi-track layout (§4.6)
├── src/
│   ├── rebuzz/                            # the library — byte-exact format primitives
│   │   ├── __init__.py                    #   public API (re-exports)
│   │   ├── blob.py                        #   MPE blob builders, note_value, NOTE_OFF
│   │   ├── blocks.py                      #   read refs, extract & mutate <Machine> blocks
│   │   ├── control.py                     #   Pedal Chord / Pedal Presetter state & pattern
│   │   └── song.py                        #   connections, sequences, splice, tempo, write
│   ├── build_limani.py                    # thin song script — single pattern/machine
│   ├── build_lastcall.py                  # thin song script — per-section patterns (§14)
│   └── pack_ps1.py                        # any .bmxml -> corruption-proof PS1 writer
└── songs/
    ├── Limani.bmxml / Write-Limani.ps1    # example output (byte-reproducible) + delivery
    └── LastCall.bmxml / Write-LastCall.ps1
```

## The one rule that matters most

**Never fabricate a `<Machine>` block — always splice a real, ReBuzz-saved one.**
Hand-written machine XML loads as a broken/uneditable machine (and Pedal Chord
throws an NRE). Every machine type the generator emits is lifted verbatim from a
file in `refs/` and then retargeted. To use a machine this repo doesn't already
have a block for, save a tiny song containing it in ReBuzz and drop that
`.bmxml` into `refs/`. See `docs/…BMXML.md` §6.

## Requirements

- **Python 3** (standard library only — no third-party packages).
- **ReBuzz Build 1827** (the format quirks here are pinned to it).
- The managed machines referenced by a given build must be **installed in
  ReBuzz** (e.g. Pedal SH101 / Faze-R / invFFT / Juno106 / Plaits / Chord /
  Presetter for Limani), and for preset automation the target's **preset bank
  (`.prs.xml`)** must be present so preset indices resolve.

## Build

```bash
python src/build_limani.py            # -> songs/Limani.bmxml
```

Paths resolve relative to the script; override with env vars if needed:

```bash
REBUZZ_REFS=/path/to/refs REBUZZ_OUT=/tmp/MySong.bmxml python src/build_limani.py
```

## Deploy to ReBuzz

Don't download the `.bmxml` directly — browser/transfer round-trips can corrupt
the bytes/BOM. Instead pack it into a PowerShell writer and run that:

```bash
python src/pack_ps1.py songs/Limani.bmxml      # -> songs/Write-Limani.ps1
```

```powershell
# on the ReBuzz machine, after placing Write-Limani.ps1 in Downloads:
Get-Content "$env:USERPROFILE\Downloads\Write-Limani.ps1" -Raw | Invoke-Expression
```

The packer embeds gzip+base64 bytes and round-trips (decode == original) before
emitting, so the file that lands in `Downloads/` is byte-identical to the build.

## Writing a new song

The format mechanics live in the **`rebuzz`** package; a song is a thin script
that imports it, declares the music + arrangement + machine wiring, and calls the
primitives. `build_limani.py` is the worked example to copy. The shape is:

```python
from rebuzz import (read, machine_blocks, lib_of, name_of, note_value as nv,
                    build_blob_mt, set_patterns, set_data, set_track_count,
                    pedal_chord_state, pedal_chord_pattern, presetter_state,
                    machines_xml, connections_xml, sequences_xml,
                    splice, set_tempo, set_loop_song_end, rename_song,
                    clear_held_notes, write_bmxml, pattern_xml)

skeleton = read("refs/synthref.bmxml")        # a real ReBuzz song to build on
blocks   = machine_blocks(skeleton)            # extract its <Machine> blocks
# ... retarget blocks, build editor blobs from your note events ...
out = splice(skeleton, machines_xml(blocks), connections_xml(srcs),
             sequences_xml(seq_machines, total_rows))
out = clear_held_notes(set_tempo(set_loop_song_end(out, total_rows), bpm, tpb))
write_bmxml("songs/MySong.bmxml", rename_song(out, "synthref", "MySong"))
```

The package surface (see each module's docstring):

- **`rebuzz.blob`** — `build_blob` / `build_blob_mt` / `build_blob_cols` (the
  byte-exact editor-blob builders), `note_value(octave, idx)`, `NOTE_OFF`.
- **`rebuzz.blocks`** — `read`, `machine_blocks`, `name_of`, `lib_of`,
  `pattern_xml`, and the block mutators `set_patterns` / `set_data` /
  `set_track_count` / `set_position` / `set_name` / `set_editor`.
- **`rebuzz.control`** — `pedal_chord_state` / `pedal_chord_pattern`,
  `presetter_state` / `presetter_clear_stored_presets`.
- **`rebuzz.song`** — `connection` / `sequence` (+ the `*_xml` joiners),
  `splice`, `set_tempo`, `set_loop_song_end`, `rename_song`,
  `clear_held_notes`, `write_bmxml`.
- **`rebuzz.validate`** — `validate(xml)` / `assert_valid(xml)` (structural +
  loop-safety checks; both builds run it before writing) and `decode_blob` for
  inspecting editor blobs. See notes §16. Tests: `python3 -m pytest tests/ -q`.
- **`rebuzz.mix`** — measurement-driven gain-staging: measure pre-fader stems
  (peak / active-RMS / LUFS / clip %) and solve the per-input bus gains for a
  target balance. CLI `python3 src/mix_report.py <stem_dir>`. Needs numpy
  (scipy optional). See notes 18.
- **`rebuzz.theory`** / **`rebuzz.dsl`** — the composition DSL: write a song from
  `Song` / `Section` / `Chords` / `Arp` / `Drums` objects (scales, chord/arp
  codes, drum step-strings, arrangement, mix, presets) and `compile()` to a
  validated `.bmxml`. No row math. See notes §17 and `src/build_dsl_demo.py`.

The order of operations (scale → numbers, pick machines, tempo/length, write
parts, assemble, verify) and every byte-level rule are in
`docs/ReBuzz_SongFormat_Notes_BMXML.md` §13 (the spec→song recipe) and §§1–12.
Running a script writes the `.bmxml`; `pack_ps1.py` then packs it for deploy.
