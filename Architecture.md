# Model Architecture and HLS Configuration

## Keras autoencoder

```
Layer        Type     Input  Output  Activation  Params
──────────────────────────────────────────────────────
enc1         Dense    128    64      ReLU        8,256
enc2         Dense    64     32      ReLU        2,080
bottleneck   Dense    32     32      ReLU        1,056
dec1         Dense    32     32      ReLU        1,056
dec2         Dense    32     64      ReLU        2,112
output       Dense    64     128     Linear      8,320
──────────────────────────────────────────────────────
Total                                            22,880
```

No BatchNorm — removed for hls4ml compatibility.  
Trained with Adam (lr=0.001), EarlyStopping patience=15, ReduceLROnPlateau.  
Final val_loss: ~0.516 on Z-score normalised FFT features.

---

## HLS4ML quantisation

All layers use `ap_fixed<8,4>`:
- 1 sign bit + 3 integer bits + 4 fractional bits
- Range: -8.0 to +7.9375
- Step: 0.0625

Strategy: `resource` — routes multiplications to DSP48E1 blocks instead of
LUT fabric. Critical for fitting the model onto xc7z020 (53,200 LUTs).

| Layer | N_IN×N_OUT | ReuseFactor | Parallel units | DSPs |
|---|---|---|---|---|
| enc1 | 128×64=8192 | 512 | 16 | 16 |
| enc2 | 64×32=2048 | 64 | 32 | 32 |
| bottleneck | 32×32=1024 | 32 | 32 | 32 |
| dec1 | 32×32=1024 | 32 | 32 | 32 |
| dec2 | 32×64=2048 | 64 | 32 | 32 |
| output | 64×128=8192 | 256 | 32 | 32 |
| **Total** | | | | **176 / 220** |

---

## TLAST wrapper

hls4ml `io_stream` does not always assert TLAST on the output stream.
Without TLAST, the AXI DMA S2MM channel waits forever.

Fix: `convert_to_hls.py` patches `myproject.cpp` after hls4ml generates it,
inserting a `myproject_axi()` wrapper that:
- Uses `ap_axiu<8,0,0,0>` streams (TDATA + TLAST + TKEEP + TSTRB)
- Unpacks 128 AXI beats into one `input_t` array write
- Calls the original `myproject()`
- Packs 128 output elements back into AXI beats
- Asserts `beat.last = 1` on beat 127 (the final output)

Top function for Vitis HLS: `myproject_axi`  
AXI-Stream ports: `in_stream` (input), `out_stream` (output)

---

## Synthesis results (Vitis HLS 2022.1)

| Resource | Used | Available | % |
|---|---|---|---|
| LUT | 43,695 | 53,200 | 82% |
| FF | 21,104 | 106,400 | 19% |
| DSP | 0 | 220 | 0% |
| BRAM | 40 | 140 | 28% |
| Timing slack | +0.65 ns | — | MET |
| Latency | 517 cycles | — | 5.17 µs @ 100 MHz |

---

## Vivado block design

```
Zynq PS (M_AXI_GP0) ──────── AXI Interconnect ──── AXI DMA (S_AXI_LITE)
Zynq PS (S_AXI_HP0) ──────── AXI Interconnect ──── AXI DMA (M_AXI_MM2S + S_AXI_S2MM)
AXI DMA (M_AXIS_MM2S) ─────────────────────────── myproject_axi (in_stream)
myproject_axi (out_stream) ─────────────────────── AXI DMA (S_AXIS_S2MM)
FCLK_CLK0 (100 MHz) ────────────────────────────── DMA aclk + NN ap_clk
FCLK_RESET0_N ──────────────────────────────────── DMA aresetn + NN ap_rst_n
```

DMA configuration:
- Scatter-gather: **disabled**
- Buffer length register: `26` bits
- Stream data width (MM2S and S2MM): `8` bits — matches `ap_axiu<8,0,0,0>`
