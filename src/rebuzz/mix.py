"""Measurement-driven gain-staging from rendered stems (the 'process' upgrade).

Render each instrument to its own pre-fader stem, point this at them, and it
measures true levels and solves the per-input bus gains needed to hit a target
balance -- instead of guessing dB trims and re-rendering. It also flags stems
that clip at the source (whose measured level is only a lower bound and which no
downstream trim can truly fix).

Requires numpy; LUFS uses scipy if present (falls back to active RMS otherwise).
This module is intentionally NOT imported by rebuzz/__init__ so the core
song-building package stays dependency-free.

    from rebuzz.mix import measure_stems, recommend_gains, format_report
    m = measure_stems({'kick': '01_kick.wav', ..., 'pad': '07_pad.wav'})
    rec = recommend_gains(m)                 # -> {name: {gain_db, amp, clipped, ...}}
    print(format_report(m, rec))
"""
import wave, struct, math

try:
    import numpy as np
except ImportError:                                       # pragma: no cover
    raise ImportError('rebuzz.mix needs numpy (pip install numpy)')


# default target balance (relative LUFS; absolute offset is normalised away).
# Foreground (kick/bass/lead) up top, pad a bed ~10 dB under, hats supporting.
DEFAULT_TARGETS = {'kick': -14, 'snare': -16, 'bass': -15, 'comp': -18,
                   'lead': -16, 'closedhats': -22, 'openhats': -24, 'pad': -26}

_UNITY = 16384


def db_to_amp(db):
    return max(1, min(_UNITY, round(_UNITY * 10 ** (db / 20.0))))


def _db(x):
    return 20 * math.log10(max(float(x), 1e-12))


def _load(path):
    w = wave.open(path, 'rb')
    sr, sw, ch, n = w.getframerate(), w.getsampwidth(), w.getnchannels(), w.getnframes()
    raw = w.readframes(n); w.close()
    if sw == 2:
        a = np.frombuffer(raw, '<i2').astype(np.float64) / 32768.0
    elif sw == 4:
        a = np.frombuffer(raw, '<i4').astype(np.float64) / 2147483648.0
    elif sw == 1:
        a = (np.frombuffer(raw, 'u1').astype(np.float64) - 128) / 128.0
    else:
        raise ValueError('unsupported sample width %d' % sw)
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return sr, a


def _kweighted_lufs(x, sr):
    try:
        from scipy.signal import lfilter
    except ImportError:
        return None
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    y = lfilter(b2, a2, lfilter(b1, a1, x))
    return -0.691 + 10 * math.log10(max(float(np.mean(y ** 2)), 1e-12))


def _active_rms(x, sr, gate_db=-50.0, block_s=0.1):
    bs = max(1, int(block_s * sr))
    e = np.array([np.sqrt(np.mean(x[i:i + bs] ** 2)) for i in range(0, len(x) - bs, bs)])
    keep = e[e > 10 ** (gate_db / 20.0)]
    return float(np.sqrt(np.mean(keep ** 2))) if len(keep) else 1e-12


def _centroid(x, sr):
    N = min(len(x), 1 << 20)
    X = np.abs(np.fft.rfft(x[:N] * np.hanning(N)))
    f = np.fft.rfftfreq(N, 1 / sr)
    return float(np.sum(f * X) / (np.sum(X) + 1e-9))


def measure(path):
    """Per-stem measurement dict (dB values, Hz, clip fraction, seconds)."""
    sr, a = _load(path)
    lufs = _kweighted_lufs(a, sr)
    return {'sr': sr, 'dur_s': len(a) / sr,
            'peak_db': _db(np.max(np.abs(a))),
            'rms_db': _db(np.sqrt(np.mean(a ** 2))),
            'active_rms_db': _db(_active_rms(a, sr)),
            'lufs': lufs,
            'centroid_hz': _centroid(a, sr),
            'clip_pct': 100.0 * float(np.sum(np.abs(a) >= 0.999)) / a.size}


def measure_stems(mapping):
    return {name: measure(path) for name, path in mapping.items()}


def recommend_gains(meas, targets=None, basis='active_rms_db', avoid_boost=True):
    """Solve per-stem bus gains to reach the target balance.

    `basis` is the measured field used for balancing (default active RMS, which
    is stable across sparse vs sustained material; 'lufs' is more perceptual but
    under-weights very transient stems). With `avoid_boost`, the whole mix is
    normalised so the loudest-needed stem sits at unity and the rest attenuate
    (no gain added, no Master clipping); raise Master to taste afterwards.
    """
    targets = targets or DEFAULT_TARGETS
    names = [n for n in meas if n in targets]
    req = {n: targets[n] - meas[n][basis] for n in names}     # dB needed to hit target
    shift = max(req.values()) if (avoid_boost and req) else 0.0
    out = {}
    for n in names:
        g = req[n] - shift
        out[n] = {'gain_db': round(g, 1), 'amp': db_to_amp(g),
                  'clipped': meas[n]['clip_pct'] > 1.0,
                  'measured_db': round(meas[n][basis], 1)}
    return out


def format_report(meas, rec=None):
    rows = ['%-12s %7s %7s %7s %7s %7s' % ('stem', 'peak', 'actRMS', 'LUFS', 'cent', 'clip%')]
    for n, m in meas.items():
        rows.append('%-12s %7.1f %7.1f %7s %7.0f %6.2f' % (
            n, m['peak_db'], m['active_rms_db'],
            ('%.1f' % m['lufs']) if m['lufs'] is not None else '-',
            m['centroid_hz'], m['clip_pct']))
    if rec:
        rows.append('')
        rows.append('%-12s %8s %6s  %s' % ('stem', 'gain dB', 'amp', 'note'))
        for n, r in rec.items():
            note = 'SOURCE CLIPPING - reduce at synth' if r['clipped'] else ''
            rows.append('%-12s %8.1f %6d  %s' % (n, r['gain_db'], r['amp'], note))
    return '\n'.join(rows)
