"""Tests for rebuzz.mix (synthetic signals, no external stem files needed)."""
import os, sys, wave, struct, math, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import numpy as np
from rebuzz.mix import measure, recommend_gains, db_to_amp


def _write_sine(path, db, freq=440, sr=48000, secs=1.0, full_scale_square=False):
    n = int(sr * secs)
    t = np.arange(n) / sr
    amp = 10 ** (db / 20.0)
    x = amp * np.sin(2 * math.pi * freq * t)
    if full_scale_square:
        x = np.sign(np.sin(2 * math.pi * freq * t))           # +-1 everywhere -> clips
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(pcm.tobytes()); w.close()


def test_peak_measurement():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 's.wav'); _write_sine(p, -6.0)
        m = measure(p)
        assert abs(m['peak_db'] - (-6.0)) < 0.3
        assert m['clip_pct'] < 0.01
        assert abs(m['rms_db'] - (-9.0)) < 0.4                # sine RMS = peak-3 dB


def test_clip_detection():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'sq.wav'); _write_sine(p, 0, full_scale_square=True)
        m = measure(p)
        assert m['clip_pct'] > 50.0


def test_db_to_amp():
    assert db_to_amp(0) == 16384
    assert db_to_amp(-6) == 8211
    assert db_to_amp(-100) >= 1 and db_to_amp(50) == 16384    # clamped to unity, never boosts


def test_recommend_relative_order():
    with tempfile.TemporaryDirectory() as d:
        loud = os.path.join(d, 'pad.wav');  _write_sine(loud, -3.0)
        quiet = os.path.join(d, 'bass.wav'); _write_sine(quiet, -24.0)
        m = {'pad': measure(loud), 'bass': measure(quiet)}
        rec = recommend_gains(m, targets={'pad': -26, 'bass': -15})
        # pad is far louder at source AND wants to be quieter -> much lower amp
        assert rec['pad']['amp'] < rec['bass']['amp']
        assert rec['pad']['gain_db'] < rec['bass']['gain_db']


if __name__ == '__main__':
    import traceback
    fails = 0
    for k, fn in sorted(globals().items()):
        if k.startswith('test_'):
            try:
                fn(); print('PASS', k)
            except Exception:
                fails += 1; print('FAIL', k); traceback.print_exc()
    sys.exit(1 if fails else 0)
