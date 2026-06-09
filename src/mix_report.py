#!/usr/bin/env python3
"""Measure a directory of pre-fader stems and print levels + recommended bus
gains. Stem files are matched to roles by stripping any leading 'NN_' prefix
(e.g. 03_closedhats.wav -> closedhats).

    python3 src/mix_report.py /path/to/stems [--basis lufs]
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebuzz.mix import measure_stems, recommend_gains, format_report

def main(argv):
    if not argv:
        print(__doc__); return 2
    d = argv[0]
    basis = 'active_rms_db'
    if '--basis' in argv:
        basis = {'lufs': 'lufs', 'rms': 'rms_db', 'peak': 'peak_db',
                 'active': 'active_rms_db'}.get(argv[argv.index('--basis') + 1], basis)
    stems = {}
    for f in sorted(os.listdir(d)):
        if f.lower().endswith('.wav'):
            name = re.sub(r'^\d+[_\- ]*', '', os.path.splitext(f)[0]).lower().replace(' ', '')
            stems[name] = os.path.join(d, f)
    if not stems:
        print('no .wav files in', d); return 1
    m = measure_stems(stems)
    print(format_report(m, recommend_gains(m, basis=basis)))
    return 0

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
