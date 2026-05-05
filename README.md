# FPGA-Based Structural Health Monitoring (Edge AI on PYNQ-Z2)

## Overview
This project implements an **anomaly detection system for vibration signals** using an **autoencoder neural network**, designed for eventual deployment on FPGA hardware.

The current stage focuses on building and validating the complete **data → model → hardware-ready pipeline** using a benchmark dataset.

---

## Current Status
- Data pipeline: ✅ Complete  
- Feature extraction: ✅ Complete  
- Model training & validation: ✅ Complete  
- HLS conversion (hls4ml): ✅ Complete  
- FPGA synthesis & deployment: ⏳ Not started  

---

## Dataset
- **Source:** Case Western Reserve University (CWRU) Bearing Dataset  
- **Data Used:**
  - 4 Normal files (~1.69M samples)
  - 3 Fault files (~366K samples)

### Achievements
- Successfully handled inconsistent `.mat` file structures  
- Built a **robust data loader** supporting multiple key formats  
- Verified signal integrity and consistency  

---

## Preprocessing Pipeline

A complete signal processing pipeline was implemented to convert raw vibration data into ML-ready features:

- Sliding Window: 1024 samples (50% overlap)  
- Hanning Window: Applied before FFT  
- FFT: 512-point → 128 frequency bins retained  
- Log Scaling: Compresses dynamic range  
- Z-score Normalization: μ = 0, σ = 1  

### Output
- 3310 normal samples  
- 710 fault samples  
- Each sample → 128-dimensional feature vector  

---

## Model: Autoencoder

A shallow dense autoencoder was designed and trained using TensorFlow/Keras.

### Architecture
- Input: 128  
- Bottleneck: 32  
- Output: 128  

### Training Setup
- Trained **only on normal data**  
- 190 epochs  
- Early stopping + learning rate scheduling  
- Loss: Mean Squared Error (MSE)  

### Results
- **100% fault detection rate**  
- **1.1% false alarm rate**  
- Clear separation between normal and fault reconstruction errors  

---

## HLS Conversion (hls4ml)

The trained model was successfully converted into synthesizable HLS C++ code.

### Configuration
- Internal precision: `ap_fixed<8,4>`  
- Output precision: `ap_fixed<16,6>`  
- AXI-Stream interface enabled  
- DATAFLOW optimisation applied  

### Output
- Complete firmware generated:
  - `myproject.cpp`
  - `parameters.h`
  - weight files  
- Verified structure for FPGA synthesis
  

## Project Structure
```
├── data/
├── preprocessing/
├── model/
│ ├── train.py
│ ├── evaluate.py
│ ├── autoencoder.h5
│ ├── threshold.npy
├── hls_project/
│ ├── firmware/
│ │ ├── myproject.cpp
│ │ ├── parameters.h
│ │ └── weights/
└── README.md
```
---

## 🧠 Key Insight

The model learns **normal vibration behavior** and detects anomalies as deviations.

> No fault labels are required during training.

---

## 🧪 Run (Software Pipeline)
```bash
python preprocessing/preprocess.py
python model/train.py
python model/evaluate.py
```
## Next Steps
Vitis HLS synthesis
Vivado block design
Bitstream generation
PYNQ deployment

## Author

Aditya Dwivedi
Electronics Engineering | VLSI & FPGA Enthusiast
---
