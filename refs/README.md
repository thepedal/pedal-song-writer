# refs/ — real ReBuzz-saved reference songs

These are genuine `.bmxml` files saved out of **ReBuzz Build 1827**, kept as
**build inputs and verification artifacts**. The generator never fabricates a
`<Machine>` block — it splices a real one out of a file here and retargets it
(the cardinal rule; see `docs/ReBuzz_SongFormat_Notes_BMXML.md` §6). Treat these
as fixed assets: they rarely change, and git diffs on the base64 blobs inside
aren't meaningful.

To support a machine this repo can't yet emit, save a minimal song containing it
in ReBuzz and add that `.bmxml` here, then splice from it.

## Build inputs (required — `build_limani.py` reads these)

| File | Carries | Used for |
|------|---------|----------|
| `synthref.bmxml` | Master + **Pedal SH101** (Bass), **Pedal Faze-R** (Lead), **Pedal invFFT** (Pad), **Pedal Juno106** (Comp), each with its pattern editor | The **song skeleton** spliced into, plus the four synth blocks. |
| `DrumTest.bmxml` | Master + 4× **Pedal Plaits** (Kick, Snare, HatClosed, HatOpen) | The drum-kit blocks (played directly). Also the **multi-pattern reference** (§14): `Kick` carries `KickLoop`+`EndKick` tiled by a 13-event sequence — proves pattern-relative positions + sequence tiling. |
| `chordref.bmxml` | Master + **Pedal Chord** (`PdlChrd`) in **chord mode** → 6-track Pedal Juno106 | The **Pedal Chord** generator template **and** the Modern Pattern Editor template; roots in col 0, chord types in col 2, target named in state. |
| `presetter_ref.bmxml` | Master + **Pedal Presetter** (1 track → Pedal Juno106, Preset 1 @ row 0) | The **Pedal Presetter** generator template; the always-16-entry `Targets` state and the colIdx-0-per-track `Preset` pattern. |
| `gainref.bmxml` | Master + **Pedal Gain Multi** + 4 generators on channels 0-3 | The multi-input **effect** reference (§15): per-input gain in the connection `<Amp>` + per-track `Amp` param; empty state blob; 8-col editor. |

Remove any of these and a fresh clone can no longer build the example song.

## Verification artifacts (not read by the build, but referenced by the docs)

| File | Carries | Documents |
|------|---------|-----------|
| `arpref.bmxml` | Master + **Pedal Chord** in **arp mode** (Mode 1 Up, Speed 2, Octaves 2 @ row 0; TPB 8) → Pedal Juno106 | The arp-mode parameters and timing the notes cite (§12). The §12 generators reproduce its blobs byte-for-byte. |
| `MasterRef.bmxml` | Master + its editor only (2 machines) | The **Master-track tempo** layout — BPM/TPB live as a pattern on the Master track, not as loadable Master parameters (§8). |
| `tracks6.bmxml` | Master + a 6-track **Pedal Juno106** | The **multi-track** blob layout — `TrackCount` plus per-track column repetition, and that the int32 after `colIdx` is the **track index** (§4.6). |

## Not included

`ref.bmxml` and `ref2.bmxml` from the original reverse-engineering are omitted:
pure early scratch, fully superseded by the notes. Recoverable from history if
ever needed.

## Note

These are skeleton/test songs authored locally; they embed third-party managed
machines only by **name and parameter values** (like a DAW project file), not the
machines themselves. The machines must be installed in ReBuzz for a generated
song to load, and a target's preset bank (`.prs.xml`) must be present for preset
indices to resolve.
