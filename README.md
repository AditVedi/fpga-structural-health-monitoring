# Structural Health Monitoring — Edge AI on PYNQ-Z2

Anomaly detection for structural health monitoring using a quantised autoencoder
deployed on a Xilinx PYNQ-Z2 FPGA board (xc7z020clg400-1).

The system learns what normal vibration looks like, then flags deviations in
real time at hardware speed (~5 µs per inference on the PL fabric).

---

## Project overview

```
Vibration signal (raw ADC samples)
        ↓
  FFT + log1p + Z-score normalisation  (PS — Python)
        ↓
  128-element feature vector
        ↓  AXI-Stream DMA
  Autoencoder NN (6 dense layers)      (PL — FPGA fabric)
        ↓  AXI-Stream DMA
  Reconstructed vector
        ↓
  MSE vs threshold → Normal / ANOMALY  (PS — Python)
```

**Phase 1 (implemented):** Pre-recorded CWRU bearing dataset used to train,
validate, and deploy the full pipeline end-to-end.

**Phase 2 (one-line swap):** Replace `load_signal()` in `pipeline.py` with a
live sensor read — everything else (preprocessing, FPGA bitstream, threshold)
is unchanged.

---

## Results

| Metric | Value |
|---|---|
| Fault detection rate | 100% (710/710 fault windows) |
| False alarm rate | 1.1% (7/662 normal windows) |
| Anomaly threshold | 0.7759 (99th percentile of normal errors) |
| Min fault MSE | 2.82 (3.6× above threshold — zero overlap) |
| FPGA inference latency | ~5.17 µs (517 cycles @ 100 MHz) |
| FPGA LUT utilisation | 82% of 53,200 (xc7z020) |
| FPGA BRAM utilisation | 28% of 140 |

---

## Repository structure

```
shm-edge-ai/
│
├── model/
│   └── validate.py       
│   └── autoencoder.h5
│   └── threshold.npy
│   └── train.py
│
├── hls_project/
│   └── convert_to_hls.py       
│   └── firmware
│       └── defines.h
│       └── myproject.cpp
│       └── myproject.h
│       └── parameters.h
│       └── weights/
│
├── preprocess/
│   └── preprocess.py
│ 
├── pynq_deploy/
│   └── pipeline.py        # runs on PYNQ-Z2 board — inference loop
│   └── autoencoder.bit
│   └── autoencoder.hwh
│   └── mixed_signal.mat
│
├── docs/
│   ├── architecture.md    # model architecture and HLS config details
│   ├── vivado_block_design.md  # step-by-step Vivado block design guide
│   └── results.md         # full results, MSE distributions, threshold analysis
│
├── data/                  # place CWRU .mat files here (gitignored)
│   ├── data.md
│
├── requirements.txt
└── README.md
```

---

## Hardware

| Component | Detail |
|---|---|
| FPGA board | PYNQ-Z2 (Digilent) |
| FPGA chip | Xilinx xc7z020clg400-1 (Zynq-7000) |
| PS | ARM Cortex-A9 dual-core @ 650 MHz |
| PL clock | 100 MHz (FCLK_CLK0) |
| DMA | AXI Direct Memory Access (scatter-gather disabled) |
| NN interface | AXI-Stream with TLAST (ap_axiu<8,0,0,0>) |

---

## Toolchain

| Tool | Version |
|---|---|
| Python | 3.9+ |
| TensorFlow / Keras | 2.10 |
| hls4ml | 0.7+ |
| Vitis HLS | 2022.1 |
| Vivado | 2022.1 |
| PYNQ | 2.7 |

---

## Reproducing from scratch

### Step 1 — Install Python dependencies

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### Step 2 — Download the CWRU dataset

Download from: https://engineering.case.edu/bearingdatacenter/download-data-file

Place these 7 files into `data/`:
- Normal: `97.mat`, `98.mat`, `100.mat`, `118.mat` → rename to `normal_0.mat` through `normal_3.mat`
- Fault:  `105.mat`, `118.mat`, `130.mat`          → rename to `IR007_0.mat`, `B007_0.mat`, `OR007@6_0.mat`

### Step 3 — Preprocess, train, validate

```bash
python preprocess.py   # creates saved/X_train.npy, X_val.npy, fault_norm.npy, train_mean.npy, train_std.npy
python train.py        # creates saved/autoencoder.h5
python Validate.py     # creates saved/threshold.npy, saved/validation_plot.png
```

Expected output from `Validate.py`:
```
Fault detection rate: 100.0%
False alarm rate:     1.1%
Threshold:            0.7759
```

### Step 4 — Generate HLS firmware

```bash
python convert_to_hls.py   # creates hls_project/firmware/
```

### Step 5 — Vitis HLS synthesis

1. Open Vitis HLS 2022.1 → Create Project
2. Add files from `hls_project/firmware/` (myproject.cpp, myproject.h, defines.h, parameters.h)
3. Set CFLAG on myproject.cpp: `-I <absolute path to hls_project/firmware>`
4. Top function: `myproject_axi`
5. Part: `xc7z020clg400-1`
6. Run C Synthesis → verify LUTs ~82%, timing met
7. Solution → Export RTL → IP Catalog

### Step 6 — Vivado block design

See `docs/vivado_block_design.md` for the complete step-by-step guide.

Block design: **Zynq PS** + **AXI DMA** + **myproject_axi NN IP**

Manual connections required:
- `DMA M_AXIS_MM2S` → `NN IP in_stream`
- `NN IP out_stream` → `DMA S_AXIS_S2MM`

Generate bitstream → collect `autoencoder.bit` and `autoencoder.hwh`.

### Step 7 — Deploy to PYNQ-Z2

Upload to board at `http://192.168.2.99` (password: `xilinx`):
```
autoencoder.bit
autoencoder.hwh
saved/threshold.npy
saved/train_mean.npy
saved/train_std.npy
data/normal_0.mat
data/IR007_0.mat
pynq_deploy/pipeline.py
```

Run:
```bash
python3 pipeline.py
```

---

## Model architecture

```
Input (128)
  Dense 128→64  ReLU   [enc1]
  Dense  64→32  ReLU   [enc2]
  Dense  32→32  ReLU   [bottleneck]
  Dense  32→32  ReLU   [dec1]
  Dense  32→64  ReLU   [dec2]
  Dense  64→128 Linear [output]
Output (128)
```

Total parameters: 22,880  
No BatchNorm (removed for hls4ml compatibility)  
Training: Adam lr=0.001, EarlyStopping patience=15

---

## HLS quantisation config

| Layer | Precision | ReuseFactor | DSPs |
|---|---|---|---|
| enc1 (128→64) | ap_fixed<8,4> | 512 | 16 |
| enc2 (64→32) | ap_fixed<8,4> | 64 | 32 |
| bottleneck (32→32) | ap_fixed<8,4> | 32 | 32 |
| dec1 (32→32) | ap_fixed<8,4> | 32 | 32 |
| dec2 (32→64) | ap_fixed<8,4> | 64 | 32 |
| output (64→128) | ap_fixed<8,4> | 256 | 32 |

Strategy: `resource` — multiplications routed to DSP48E1 blocks, not LUT fabric.

---

## Dataset

**CWRU Bearing Dataset** — Case Western Reserve University  
https://engineering.case.edu/bearingdatacenter

| File | Type | Channel | Samples |
|---|---|---|---|
| normal_0.mat | Normal | X097_DE_time | 243,938 |
| normal_1.mat | Normal | X098_DE_time | 483,903 |
| normal_2.mat | Normal | X098_DE_time | 483,903 |
| normal_3.mat | Normal | X100_DE_time | 485,643 |
| B007_0.mat | Ball fault | X118_DE_time | 122,571 |
| IR007_0.mat | Inner race | X105_DE_time | 121,265 |
| OR007@6_0.mat | Outer race | X130_DE_time | 121,991 |

Preprocessing: sliding window (1024 samples, 50% overlap) → Hanning window →
FFT → log1p → Z-score normalise using training set statistics.

---

## Relevance to structural health monitoring

The CWRU bearing dataset was used as a training ground because it is clean,
labelled, and freely available. The neural network did not learn anything
specific about bearings — it learned to model normal vibration and flag
deviations. This skill transfers directly to any vibrating structure (bridges,
buildings, pipelines, rotating machinery) by collecting normal recordings from
that structure and retraining. The FPGA hardware, Python code, preprocessing,
and AXI data path are all unchanged.
