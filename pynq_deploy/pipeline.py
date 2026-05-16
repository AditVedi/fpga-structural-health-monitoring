import numpy as np
import scipy.io
import time
from pynq import Overlay, allocate

# ── Load overlay ─────────────────────────────────────────────
print("Loading overlay...")
ol        = Overlay('autoencoder.bit')
dma       = ol.axi_dma_0
threshold = float(np.load('threshold.npy'))
mean      = np.load('train_mean.npy')
std       = np.load('train_std.npy')
print(f"Overlay loaded. Threshold: {threshold:.4f}")

# ── Preprocessing (identical to your training pipeline) ──────
WINDOW = 1024
N_BINS = 128

def preprocess(raw):
    hann     = np.hanning(WINDOW).astype(np.float32)
    spectrum = np.abs(np.fft.rfft(raw * hann))[:N_BINS]
    spectrum = np.log1p(spectrum).astype(np.float32)
    return ((spectrum - mean) / (std + 1e-8)).astype(np.float32)

# ── FPGA inference ────────────────────────────────────────────
def fpga_infer(features):
    in_buf  = allocate(shape=(N_BINS,), dtype=np.float32)
    out_buf = allocate(shape=(N_BINS,), dtype=np.float32)
    in_buf[:] = features
    dma.sendchannel.transfer(in_buf)
    dma.recvchannel.transfer(out_buf)
    dma.sendchannel.wait()
    dma.recvchannel.wait()
    result = np.array(out_buf)
    in_buf.freebuffer()
    out_buf.freebuffer()
    return result

# ── Data source (Phase 1 — file replay) ──────────────────────
def load_signal(path):
    mat  = scipy.io.loadmat(path)
    # Try all DE_time key variants from your CWRU files
    for key in mat:
        if key.endswith('DE_time'):
            return mat[key].flatten().astype(np.float32)
    raise ValueError(f"No DE_time channel found in {path}")

# ── Change this line to switch files ─────────────────────────
signal = load_signal('normal_0.mat')   # swap to IR007_0.mat to test fault detection
cursor = 0

# ── Main inference loop ───────────────────────────────────────
print("Running inference — Ctrl+C to stop\n")
try:
    while True:
        if cursor + WINDOW > len(signal):
            cursor = 0

        raw      = signal[cursor : cursor + WINDOW]
        features = preprocess(raw)
        recon    = fpga_infer(features)
        mse      = float(np.mean((features - recon) ** 2))
        cursor  += 512   # 50% overlap, same as training

        if mse > threshold:
            print(f"ANOMALY  MSE={mse:.4f}  threshold={threshold:.4f}")
            ol.leds[0].on()
        else:
            print(f"Normal   MSE={mse:.4f}  threshold={threshold:.4f}")
            ol.leds[0].off()

        time.sleep(0.05)   # 50ms between windows

except KeyboardInterrupt:
    print("\nStopped.")
    ol.leds[0].off()
