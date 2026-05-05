import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from tensorflow import keras
import os

# ── Load model and data ───────────────────────────────────────
model      = keras.models.load_model('saved/autoencoder.h5')
X_val      = np.load('saved/X_val.npy')
fault_norm = np.load('saved/fault_norm.npy')

print(f"Normal val windows: {X_val.shape[0]}")
print(f"Fault windows:      {fault_norm.shape[0]}\n")

# ── Compute reconstruction error for each window ──────────────
def recon_error(data):
    pred = model.predict(data, verbose=0)
    return np.mean((data - pred) ** 2, axis=1)

normal_err = recon_error(X_val)
fault_err  = recon_error(fault_norm)

# ── Print error statistics ────────────────────────────────────
print("Normal reconstruction error:")
print(f"  Mean:   {normal_err.mean():.6f}")
print(f"  Median: {np.median(normal_err):.6f}")
print(f"  99th%:  {np.percentile(normal_err, 99):.6f}")

print("\nFault reconstruction error:")
print(f"  Mean:   {fault_err.mean():.6f}")
print(f"  Median: {np.median(fault_err):.6f}")
print(f"  Min:    {fault_err.min():.6f}")

# ── Set threshold at 99th percentile of normal errors ─────────
threshold = np.percentile(normal_err, 99)
print(f"\nThreshold (99th pct of normal): {threshold:.6f}")

# ── Detection rates ───────────────────────────────────────────
detected   = np.sum(fault_err  > threshold)
false_alrm = np.sum(normal_err > threshold)

detect_rate = detected   / len(fault_err)  * 100
false_rate  = false_alrm / len(normal_err) * 100

print(f"\nFault detection rate: {detect_rate:.1f}%  "
      f"({detected}/{len(fault_err)} fault windows caught)")
print(f"False alarm rate:     {false_rate:.1f}%  "
      f"({false_alrm}/{len(normal_err)} normal windows misflagged)")

# ── Per fault-type breakdown ──────────────────────────────────
# fault_norm has 3 fault types stacked: B007, IR007, OR007
n = len(fault_norm) // 3
names = ['B007 (ball fault)', 'IR007 (inner race)', 'OR007 (outer race)']
print("\nPer fault type:")
for i, name in enumerate(names):
    chunk = fault_err[i*n : (i+1)*n]
    rate  = np.sum(chunk > threshold) / len(chunk) * 100
    print(f"  {name}: {rate:.1f}% detected  (mean err={chunk.mean():.4f})")

# ── Save threshold ────────────────────────────────────────────
np.save('saved/threshold.npy', threshold)
print(f"\nThreshold saved to saved/threshold.npy")

# ── Histogram plot ────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4))

# Left: overlapping histogram
ax1.hist(normal_err, bins=60, alpha=0.7,
         color='steelblue', label='Normal', density=True)
ax1.hist(fault_err,  bins=60, alpha=0.7,
         color='tomato',    label='Fault',  density=True)
ax1.axvline(threshold, color='black', linestyle='--', linewidth=1.5,
             label=f'Threshold={threshold:.4f}')
ax1.set_xlabel('Reconstruction error (MSE)')
ax1.set_ylabel('Density')
ax1.set_title('Normal vs fault — error distribution')
ax1.legend()

# Right: per-fault-type box plot
fault_chunks = [fault_err[i*n:(i+1)*n] for i in range(3)]
all_data  = [normal_err] + fault_chunks
all_labels = ['Normal', 'Ball\nfault', 'Inner\nrace', 'Outer\nrace']
bp = ax2.boxplot(all_data, tick_labels=all_labels, patch_artist=True,
                  medianprops=dict(color='black', linewidth=2))
colors = ['steelblue', 'tomato', 'tomato', 'tomato']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax2.axhline(threshold, color='black', linestyle='--',
             linewidth=1.5, label=f'Threshold')
ax2.set_ylabel('Reconstruction error (MSE)')
ax2.set_title('Error by fault type')
ax2.legend()

plt.tight_layout()
plt.savefig('saved/validation_plot.png', dpi=150)
plt.show()
print("Plot saved to saved/validation_plot.png")

# ── Final verdict ─────────────────────────────────────────────
print("\n══ VERDICT ══════════════════════════════")
if detect_rate >= 85 and false_rate <= 5:
    print("PASS — model is ready for FPGA deployment")
elif detect_rate >= 70:
    print("MARGINAL — workable but worth improving")
else:
    print("FAIL — model needs retraining, paste output for diagnosis")
print(f"Detection: {detect_rate:.1f}%   False alarms: {false_rate:.1f}%")