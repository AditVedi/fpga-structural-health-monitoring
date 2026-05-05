import numpy as np
import hls4ml
import shutil, os
from tensorflow import keras

# ── Stage 1 ───────────────────────────────────────────────────
print("Stage 1 — loading model...")
model     = keras.models.load_model('saved/autoencoder.h5')
threshold = float(np.load('saved/threshold.npy'))
print(f"Threshold: {threshold:.6f}")

# ── Stage 2 ───────────────────────────────────────────────────
print("\nStage 2 — configuring...")
config = hls4ml.utils.config_from_keras_model(model, granularity='name')

for layer in config['LayerName']:
    config['LayerName'][layer]['Precision']   = 'ap_fixed<8,4>'
    config['LayerName'][layer]['ReuseFactor'] = 1
config['LayerName']['output']['Precision'] = 'ap_fixed<16,6>'
print("Precision set.")

# ── Stage 3 ───────────────────────────────────────────────────
print("\nStage 3 — converting and writing HLS files...")
if os.path.exists('hls_project'):
    shutil.rmtree('hls_project')
    print("Cleared old hls_project/")

hls_model = hls4ml.converters.convert_from_keras_model(
    model,
    hls_config=config,
    output_dir='hls_project',
    part='xc7z020clg400-1',
    io_type='io_stream',
    backend='Vivado'
)

# This writes all C++ files to disk — no GCC needed
hls_model.write()
print("HLS files written to hls_project/")

# ── Verify files exist ────────────────────────────────────────
print("\nFiles created:")
for root, dirs, files in os.walk('hls_project'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    level = root.replace('hls_project', '').count(os.sep)
    indent = '  ' * level
    print(f"{indent}{os.path.basename(root)}/")
    for f in files:
        size = os.path.getsize(os.path.join(root, f))
        print(f"{indent}  {f}  ({size:,} bytes)")
