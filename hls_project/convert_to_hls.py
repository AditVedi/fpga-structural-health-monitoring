"""
convert_to_hls.py  —  Structural Health Monitoring, PYNQ-Z2

Generates hls4ml firmware and patches a DMA-compatible AXI-stream
wrapper with proper TLAST support.

Top function after patching:
    myproject_axi
"""

import numpy as np
import hls4ml
import shutil
import os
from tensorflow import keras

# ============================================================================
# Stage 1 — Load model
# ============================================================================
print("Stage 1 — loading model...")

model = keras.models.load_model(
    'saved/autoencoder.h5',
    compile=False
)

threshold = float(np.load('saved/threshold.npy'))

print(f"  Threshold : {threshold:.6f}")

model.summary()

# ============================================================================
# Stage 2 — Configure hls4ml
# ============================================================================
print("\nStage 2 — configuring hls4ml...")

config = hls4ml.utils.config_from_keras_model(
    model,
    granularity='name'
)

for layer in config['LayerName']:
    config['LayerName'][layer]['Precision']   = 'ap_fixed<8,4>'
    config['LayerName'][layer]['Strategy']    = 'resource'
    config['LayerName'][layer]['ReuseFactor'] = 64

config['LayerName']['enc1']['ReuseFactor']       = 512
config['LayerName']['enc2']['ReuseFactor']       = 64
config['LayerName']['bottleneck']['ReuseFactor'] = 32
config['LayerName']['dec1']['ReuseFactor']       = 32
config['LayerName']['dec2']['ReuseFactor']       = 64
config['LayerName']['output']['ReuseFactor']     = 256

# ============================================================================
# Stage 3 — Convert model
# ============================================================================
print("\nStage 3 — converting to HLS...")

if os.path.exists('hls_project'):
    shutil.rmtree('hls_project')
    print("  Cleared old hls_project/")

hls_model = hls4ml.converters.convert_from_keras_model(
    model,
    hls_config=config,
    output_dir='hls_project',
    part='xc7z020clg400-1',
    io_type='io_stream',
    backend='Vivado'
)

hls_model.write()

print("  HLS files written.")

# ============================================================================
# Stage 4 — Patch TLAST AXI wrapper
# ============================================================================
print("\nStage 4 — patching TLAST AXI wrapper...")

CPP_PATH = 'hls_project/firmware/myproject.cpp'
H_PATH   = 'hls_project/firmware/myproject.h'

N_IN  = 128
N_OUT = 128

# ============================================================================
# Read original cpp
# ============================================================================
with open(CPP_PATH, 'r', encoding='utf-8') as f:
    cpp_content = f.read()

# ============================================================================
# AXI wrapper
# ============================================================================
AXI_WRAPPER = f"""
// ============================================================================
// DMA-compatible AXI-stream wrapper with TLAST
// ============================================================================

#include "ap_axi_sdata.h"

typedef ap_axiu<8,0,0,0> axi_word_t;

void myproject_axi(
    hls::stream<axi_word_t> &in_stream,
    hls::stream<axi_word_t> &out_stream
)
{{
#pragma HLS INTERFACE axis port=in_stream
#pragma HLS INTERFACE axis port=out_stream
#pragma HLS INTERFACE ap_ctrl_none port=return

    hls::stream<input_t> inner_in("inner_in");
    hls::stream<result_t> inner_out("inner_out");

#pragma HLS STREAM variable=inner_in depth=1
#pragma HLS STREAM variable=inner_out depth=1

    // =========================================================================
    // Read ONE full input vector
    // =========================================================================
    input_t in_vec;

    for (int i = 0; i < {N_IN}; i++) {{
#pragma HLS PIPELINE II=1

        axi_word_t beat = in_stream.read();

        in_vec[i] = *reinterpret_cast<input_t::value_type*>(&beat.data);
    }}

    inner_in.write(in_vec);

    // =========================================================================
    // Run neural network
    // =========================================================================
    myproject(inner_in, inner_out);

    // =========================================================================
    // Read ONE full output vector
    // =========================================================================
    result_t out_vec = inner_out.read();

    // =========================================================================
    // Stream output vector with TLAST
    // =========================================================================
    for (int i = 0; i < {N_OUT}; i++) {{
#pragma HLS PIPELINE II=1

        axi_word_t beat;

        beat.data = *reinterpret_cast<ap_uint<8>*>(&out_vec[i]);

        beat.keep = 1;
        beat.strb = 1;
        beat.last = (i == {N_OUT} - 1);

        out_stream.write(beat);
    }}
}}

// ============================================================================
// End AXI wrapper
// ============================================================================

"""

# ============================================================================
# Insert wrapper after includes
# ============================================================================
insert_after = '#include "parameters.h"'

if insert_after in cpp_content:

    cpp_content = cpp_content.replace(
        insert_after,
        insert_after + '\n\n' + AXI_WRAPPER
    )

else:
    raise RuntimeError(
        'Could not find #include "parameters.h" in myproject.cpp'
    )

# ============================================================================
# Write patched cpp
# ============================================================================
with open(CPP_PATH, 'w', encoding='utf-8') as f:
    f.write(cpp_content)

print(f"  Patched: {CPP_PATH}")

# ============================================================================
# Patch header
# ============================================================================
with open(H_PATH, 'r', encoding='utf-8') as f:
    h_content = f.read()

AXI_DECL = """
// ============================================================================
// AXI wrapper declaration
// ============================================================================

#include "ap_axi_sdata.h"

typedef ap_axiu<8,0,0,0> axi_word_t;

void myproject_axi(
    hls::stream<axi_word_t> &in_stream,
    hls::stream<axi_word_t> &out_stream
);

"""

h_content = h_content.replace(
    '#endif',
    AXI_DECL + '\n#endif'
)

with open(H_PATH, 'w', encoding='utf-8') as f:
    f.write(h_content)

print(f"  Patched: {H_PATH}")

# ============================================================================
# Stage 5 — Verify
# ============================================================================
print("\nStage 5 — verifying files...")

required = [
    'hls_project/firmware/myproject.cpp',
    'hls_project/firmware/myproject.h',
]

all_ok = True

for f in required:

    ok = os.path.exists(f)

    print(f"  {'OK' if ok else 'MISSING'} : {f}")

    if not ok:
        all_ok = False

with open(CPP_PATH, 'r', encoding='utf-8') as f:
    patched = f.read()

if 'myproject_axi' in patched and 'beat.last' in patched:
    print("  OK : TLAST wrapper confirmed")
else:
    print("  ERROR : wrapper missing")
    all_ok = False

# ============================================================================
# Stage 6 — Final instructions
# ============================================================================
print("""
=================================================================
  Expected resource usage
-----------------------------------------------------------------
  LUTs  : ~43k-50k
  FFs   : ~21k-35k
  DSPs  : ~0-176
  BRAMs : ~40
=================================================================
""")
