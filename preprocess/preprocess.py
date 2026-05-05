import scipy.io
import numpy as np
import os
from sklearn.model_selection import train_test_split

# ── Settings ──────────────────────────────────────────────────
WINDOW      = 1024   # samples per chunk
STEP        = 512    # 50% overlap
N_BINS      = 128    # FFT bins to keep
MIN_SAMPLES = 1000   # skip files shorter than this

# ── Part A: Smart loader ──────────────────────────────────────
def find_de_channel(mat):
    keys = [k for k in mat if not k.startswith('_')]
    if 'DE_time' in keys:
        return 'DE_time'
    for k in keys:
        if k.endswith('DE_time'):
            return k
    for k in keys:
        if 'DE' in k:
            return k
    return max(keys, key=lambda k: np.array(mat[k]).size)

def load_mat_robust(path):
    mat = scipy.io.loadmat(path)
    ch  = find_de_channel(mat)
    sig = np.array(mat[ch]).flatten().astype(np.float32)
    if len(sig) < MIN_SAMPLES:
        print(f"  SKIPPED {os.path.basename(path)}"
              f" — only {len(sig)} samples (channel='{ch}')")
        return None
    print(f"  OK  {os.path.basename(path)}"
          f" — {len(sig):,} samples  channel='{ch}'")
    return sig

print("Loading NORMAL files:")
normal_signals = []
for f in sorted(os.listdir('data/normal')):
    if not f.endswith('.mat'): continue
    sig = load_mat_robust(f'data/normal/{f}')
    if sig is not None:
        normal_signals.append(sig)

print(f"\nLoading FAULT files:")
fault_signals = []
for f in sorted(os.listdir('data/fault')):
    if not f.endswith('.mat'): continue
    sig = load_mat_robust(f'data/fault/{f}')
    if sig is not None:
        fault_signals.append(sig)

if len(normal_signals) == 0:
    raise RuntimeError("No usable normal files found.")

# ── Part B: Window + FFT ──────────────────────────────────────
def signal_to_windows(signal):
    hann   = np.hanning(WINDOW).astype(np.float32)
    frames = []
    for start in range(0, len(signal) - WINDOW, STEP):
        chunk    = signal[start : start + WINDOW]
        windowed = chunk * hann
        spectrum = np.abs(np.fft.rfft(windowed))[:N_BINS]
        spectrum = np.log1p(spectrum).astype(np.float32)
        frames.append(spectrum)
    return np.array(frames, dtype=np.float32)

print("\nConverting to FFT windows...")
normal_windows = np.concatenate(
    [signal_to_windows(s) for s in normal_signals]
)
fault_windows = np.concatenate(
    [signal_to_windows(s) for s in fault_signals]
)
print(f"Normal windows: {normal_windows.shape}")
print(f"Fault windows:  {fault_windows.shape}")

# ── Part C: Normalize + save ──────────────────────────────────
print("\nNormalizing...")
train_mean = normal_windows.mean(axis=0)
train_std  = normal_windows.std(axis=0) + 1e-8

normal_norm = (normal_windows - train_mean) / train_std
fault_norm  = (fault_windows  - train_mean) / train_std

print(f"Sanity check — normal_norm:"
      f"  mean={normal_norm.mean():.4f}"
      f"  std={normal_norm.std():.4f}"
      f"  (should be ≈0.0 and ≈1.0)")

X_train, X_val = train_test_split(
    normal_norm, test_size=0.2, random_state=42
)

os.makedirs('saved', exist_ok=True)
np.save('saved/train_mean.npy',  train_mean)
np.save('saved/train_std.npy',   train_std)
np.save('saved/X_train.npy',     X_train)
np.save('saved/X_val.npy',       X_val)
np.save('saved/fault_norm.npy',  fault_norm)

print(f"\n── Saved to saved/ ──────────────────")
print(f"  X_train:    {X_train.shape}")
print(f"  X_val:      {X_val.shape}")
print(f"  fault_norm: {fault_norm.shape}")
print(f"  train_mean: {train_mean.shape}")
print(f"  train_std:  {train_std.shape}")
print("\nDone. Run step3_train.py next.")
