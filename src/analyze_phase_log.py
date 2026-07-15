#!/usr/bin/env python3
"""Analyze C:\\temp\\phase_perf.log from the diag/phase-probe rig.

Usage:  python3 analyze_phase_log.py phase_perf.log [samplerate]

Only the LAST session in the file is analyzed (each launch appends a
'# session' header). Budget per fill is computed from that fill's own frame
count, so mixed driver buffer sizes are handled.
"""
import sys
import statistics as st
from collections import Counter

RATE = int(sys.argv[2]) if len(sys.argv) > 2 else 44100
path = sys.argv[1] if len(sys.argv) > 1 else "phase_perf.log"

COLS = ["lockWaitUs", "fillUs", "readWorkUs", "colEvUs", "tickUs",
        "patPosUs", "hostInfoUs", "tapUs", "waveUs", "otherUs"]
# columns that can "own" a spike (fillUs is the sum-side, not a phase)
PHASES = ["lockWaitUs", "readWorkUs", "colEvUs", "tickUs",
          "patPosUs", "hostInfoUs", "tapUs", "waveUs", "otherUs"]

rows = []
with open(path) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith("tMs"):
            rows = []  # new session: keep only the last one
            continue
        p = line.split(",")
        r = {"tMs": float(p[0])}
        for c, v in zip(COLS, p[1:11]):
            r[c] = int(v)
        r["chunks"] = int(p[11])
        r["samples"] = int(p[12])
        rows.append(r)

if not rows:
    sys.exit("no data rows found")

for r in rows:
    r["budgetUs"] = r["samples"] / RATE * 1e6
    r["totalUs"] = r["lockWaitUs"] + r["fillUs"]  # wall time incl. lock wait

n = len(rows)
dur = sum(r["samples"] for r in rows) / RATE
print(f"{n} fills, {dur:.1f} s of audio, budget/fill ~{rows[0]['budgetUs']:.0f} us "
      f"({rows[0]['samples']} frames @ {RATE} Hz)")

print("\nper-fill stats (us):")
print(f"  {'column':12s} {'mean':>9s} {'p99':>9s} {'max':>9s} {'share':>7s}")
mean_total = st.mean(r["totalUs"] for r in rows)
for c in COLS:
    vals = sorted(r[c] for r in rows)
    print(f"  {c:12s} {st.mean(vals):9.1f} {vals[int(n*0.99)]:9d} {vals[-1]:9d} "
          f"{100*st.mean(vals)/mean_total:6.1f}%")

spikes = [r for r in rows if r["totalUs"] > r["budgetUs"]]
print(f"\nover-budget fills (dropout proxies): {len(spikes)} / {n} "
      f"({100*len(spikes)/n:.1f}%)")

if spikes:
    dom = Counter(max(PHASES, key=lambda c: r[c]) for r in spikes)
    print("dominant phase in over-budget fills:")
    for c, k in dom.most_common():
        print(f"  {c:12s} {k}")

    big = [r for r in spikes if r["totalUs"] > 4 * r["budgetUs"]]
    print(f"\nbig spikes (>4x budget): {len(big)}")
    if len(big) > 2:
        iv = [round(b["tMs"] - a["tMs"], 1) for a, b in zip(big, big[1:])]
        print(f"inter-spike intervals (ms): median {st.median(iv):.0f}, "
              f"mean {st.mean(iv):.0f}")
        print(f"first 20 intervals: {iv[:20]}")
        # the 512 ms question, answered directly
        near512 = sum(1 for x in iv if 384 <= x <= 640)
        print(f"intervals within 512 +/- 128 ms: {near512}/{len(iv)}")
    print("\nworst 10 fills:")
    print("  tMs        totalUs  dominant      lockWait readWork colEv  tick   patPos hostInfo tap    other")
    for r in sorted(spikes, key=lambda r: -r["totalUs"])[:10]:
        d = max(PHASES, key=lambda c: r[c])
        print(f"  {r['tMs']:10.1f} {r['totalUs']:8d} {d:13s} "
              f"{r['lockWaitUs']:8d} {r['readWorkUs']:8d} {r['colEvUs']:6d} "
              f"{r['tickUs']:6d} {r['patPosUs']:6d} {r['hostInfoUs']:8d} "
              f"{r['tapUs']:6d} {r['otherUs']:6d}")
