# rebuzz-songgen — Project Overview

The front door. This is the *map*: what the project is, how the parts stack, the
workflow loop, and the rules that must not be broken. For depth, follow the
pointers in [§7](#7-where-to-look). Keep this file short — a map, not the
territory.

---

## 1. What this is, and what to trust

Generate **loadable ReBuzz `.bmxml` songs programmatically**, from a byte-exact
understanding of the format — and keep the toolkit reusable enough to commission
arbitrary songs (style / key / tempo / instruments) rather than one-offs.

Be honest about confidence; the layers are not equal:

| Layer | Confidence | Why |
|-------|-----------|-----|
| **File structure** (machines, routing, patterns, blobs) | very high | verified byte-exact against real ReBuzz saves; `validate()` enforces it |
| **Mix** (levels, balance, peaks, timing) | now measurable | the render → stem → `rebuzz.mix` loop replaced ear-guessing with numbers |
| **Musical quality** (does it sound good) | low / unverifiable here | composed blind — Claude cannot hear; only a human render confirms it |

### The cardinal rule

**Never fabricate a `<Machine>` block. Splice a real one.** Every machine in
every song is lifted verbatim from a real ReBuzz save in `refs/`. Hand-building a
machine block from scratch is what caused the original null-reference crash, and
it stays banned. New machine ⇒ get a real save of it first (see `refs/MACHINES.md`).

---

## 2. How the pieces stack

```
            theory ── notes/scales/chords ─┐
                                           ├─► dsl ── Song/Section/voices ──► compile() ─┐
  blob ── editor-blob bytes ──┐            │                                             │
  blocks ── <Machine> edits ──┼─► song ── splice / connect / sequence ──────────────────┼─► .bmxml
  control ── chord/presetter ─┘            │                                             │
                                           validate() ── 8 structural+loop checks ◄──────┘
                                           mix ── measure stems, solve bus gains (offline, numpy)
```

| Module (`src/rebuzz/`) | Role |
|---|---|
| `blob.py` | byte-exact Modern-Pattern-Editor blob builders; `note_value`, `NOTE_OFF` |
| `blocks.py` | read a save; find/extract/edit `<Machine>` blocks; `find_machine`, `set_param`, positions, `assert_no_overlap` |
| `control.py` | Pedal Chord / Pedal Presetter state + patterns (machines that drive other machines) |
| `song.py` | connections, sequences, `splice`, tempo, loop-end, held-note clear, `write_bmxml` |
| `theory.py` | note parsing, scales/modes, chord & arp-mode code tables, `Scale` |
| `dsl.py` | `Song / Section / Chords / Arp / Drums` → `compile()`; the musical front end |
| `validate.py` | `validate` / `assert_valid` (structural + loop-safety), `decode_blob` |
| `mix.py` | measure pre-fader stems (peak/RMS/LUFS/clip), solve bus gains; **offline tool, needs numpy, not auto-imported** |

Lower rows are primitives; `dsl` and `mix` are the layers a human actually drives.

---

## 3. The workflow loop

```
 compose ─► build ─► validate ─► deliver ─► render ─► measure ─► trim / limit ─► (repeat)
  (DSL or   (splice   (assert_   (pack_ps1  (human,   (mix_      (set bus gains,
  build_*)  blocks)   valid)     → ReBuzz)  to wav)   report)    limiter ceiling)
```

- **compose** — a `Song` in the DSL, or a hand-written `build_*.py` for full control.
- **build** — splice real blocks, attach editor blobs, wire connections + sequences.
- **validate** — `assert_valid` runs before every write; a wiring or loop bug fails
  the build instead of surfacing inside ReBuzz.
- **deliver** — `pack_ps1.py` wraps the `.bmxml` in a PowerShell writer (browsers
  corrupt the file; the BOM and bytes must survive). User runs it in `Downloads`.
- **render** — the human renders in ReBuzz, ideally **pre-fader stems**.
- **measure** — `mix_report.py` reports true levels and solves the bus gains.
- **trim / limit** — apply gains to the gain buses; the Pedal Limit caps peaks.

Claude closes every loop it can offline (structure, levels, peaks, timing); only
subjective musical quality needs the human ear.

---

## 4. Invariants (don't break these)

1. **Splice, never fabricate** machine blocks (§1).
2. **`assert_valid` before `write_bmxml`** — every build script does this.
3. **Loop-safety** (notes §12.9.1): a held-note generator that gets no note-on at
   song tick 0 carries a row-0 note-off on *every* track, or it drones on loop.
4. **Gain-stage from measurement**, not by ear — and watch for *source* clipping
   (a clipped stem means no downstream trim can truly fix it).
5. **Deterministic builds** — re-running a build yields identical bytes; tests
   assert this, and `Limani.bmxml` has a byte-baseline.
6. **Delivery via PowerShell**, UTF-8 BOM preserved. **Commit messages contain no
   double quotes.**
7. **Playable notes live in the MPE blob**, not the PatternCore `<Columns>` (which
   ReBuzz ignores at playback).

---

## 5. Repo layout

```
src/rebuzz/        the library (modules in §2)
src/build_*.py     song builds: limani, lastcall, dsl_demo, machine_ref
src/catalog_machines.py   refs/MACHINES.md generator
src/mix_report.py  stem-measurement CLI
src/pack_ps1.py    .bmxml → PowerShell writer
refs/              real ReBuzz saves spliced into songs (the only legal machine source)
  MachineRef.bmxml   one instance of every available machine — the splice source
  MACHINES.md        generated catalog: type, params/ranges, note column per machine
songs/             built .bmxml + their Write-*.ps1
tests/             pytest: validate / dsl / mix (20 tests; determinism + byte-identity)
docs/              ReBuzz_SongFormat_Notes_BMXML.md (the deep format/technique reference)
```

Songs shipped: **Limani** (D-Hijaz, single-pattern) and **Last Call** (A-blues,
sectioned, submix buses + master limiter); **DslDemo** (authored via the DSL).

---

## 6. Conventions worth knowing

- Machines are spliced from `refs/`; new machines are added to `MachineRef.bmxml`,
  then `catalog_machines.py` regenerates `MACHINES.md`.
- A generator's **note column = (#Global params) + (Note's index among Track
  params)** — derivable statically from the catalog, no need to enter-and-decode.
- Submix topology: generators → gain bus → (limiter) → Master; per-input gain
  lives in both the connection `Amp` and the machine's per-track `Amp`, kept equal.
- dB → amp: `16384 = unity`; `amp = round(16384 · 10^(dB/20))`.

---

## 7. Where to look

| Need | Document |
|------|----------|
| Install, quickstart, package surface | `README.md` |
| Byte layout, recipes, control machines, effects, DSL, mixing, limiter | `docs/ReBuzz_SongFormat_Notes_BMXML.md` §§1–19 |
| Per-machine params / note columns / ranges | `refs/MACHINES.md` |
| Which real saves exist and what they're for | `refs/README.md` |
| Broader ReBuzz machine-development notes (Roster, Core, Build, addenda) | project knowledge (outside this repo) |

Format-notes quick index: §§1–9 format & assembly · §10 Limani design ·
§11 error chronology · §12 control machines · §13 spec→song recipe ·
§14 multi-pattern · §15 effects/buses · §16 validation · §17 DSL ·
§18 measurement-driven mixing · §19 master limiter.

---

## 8. Status & open frontiers

**Done:** byte-exact format model · the `rebuzz` library · a composition DSL ·
structural + loop-safety validation · measurement-driven gain-staging · a master
chain (buses → limiter → Master) · a 34-machine catalog spliceable on demand.

**Open (roughly in leverage order):**
- A **real melodic lead** programmed directly into Faze-R / FM / Add-R (vs the
  current Pedal-Chord arp) — the biggest single musical upgrade.
- **Serial FX** chains now that reverbs/delays/EQ/compressors are catalogued.
- **Per-section voicing** overrides and a **direct-note lead voice** in the DSL.
- **`compose(spec)`** — fold `rig()` + the DSL into a one-call commission entry point.
- Add the four machines still missing from `MachineRef`: **M1, PeerCtrl, LFO, Muter**.
- Fold the limiter into the DSL (`Song.limiter(...)`).
