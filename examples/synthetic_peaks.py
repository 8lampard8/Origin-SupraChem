"""Public synthetic demonstration; no experimental data or Origin required."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from spectra import highest_peak, variance_summary

x = list(range(390, 551))
peaks = []
for amplitude in [100, 110, 90, 105]:
    y = [amplitude * math.exp(-((w-460)/18)**2) for w in x]
    peak = highest_peak(x, y, threshold=420)
    assert peak is not None
    peaks.append(peak["intensity"])
    print(peak)
print(variance_summary(peaks))
