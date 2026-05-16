# Vivado Block Design Guide

Vivado 2022.1. Target: xc7z020clg400-1 (PYNQ-Z2).

## Prerequisites

- Vitis HLS IP exported to `autoencoder_hls/solution1/impl/ip/`  
  (must contain `component.xml`)
- PYNQ-Z2 board files installed (optional — can use part directly)

---

## Step 1 — Create Vivado project

Create Project → RTL Project → Do not specify sources  
Board tab → PYNQ-Z2 (or Parts tab → xc7z020clg400-1)

---

## Step 2 — Register NN IP

Tools → Settings → IP → Repository → + →  
navigate to `autoencoder_hls/solution1/impl/ip/` → Select  
Confirm: "1 IP definition found" → OK

---

## Step 3 — Create Block Design

Flow Navigator → IP INTEGRATOR → Create Block Design → name: `design_1` → OK

---

## Step 4 — Add Zynq PS

Ctrl+I → search `zynq` → add ZYNQ7 Processing System  
Run Block Automation → Apply Board Preset → OK

Double-click Zynq block:
- PS-PL Configuration → HP Slave AXI Interface → enable **S AXI HP0**
- Clock Configuration → PL Fabric Clocks → FCLK_CLK0 = **100 MHz**
- OK

---

## Step 5 — Add AXI DMA

Ctrl+I → search `axi dma` → add AXI Direct Memory Access

Double-click DMA:
- Uncheck **Enable Scatter Gather Engine**
- Width of Buffer Length Register = `26`
- Read Channel (MM2S): Memory Map Data Width = `32`, Stream Data Width = `8`
- Write Channel (S2MM): Memory Map Data Width = `32`, Stream Data Width = `8`
- OK

Stream Data Width = 8 is critical — the NN IP uses `ap_axiu<8,0,0,0>` (8-bit beats).

---

## Step 6 — Add NN IP

Ctrl+I → search `myproject` → add it  
Ports visible: `in_stream` (input), `out_stream` (output)

---

## Step 7 — Run Connection Automation

Click green banner → All Automation → OK

Vivado auto-wires:
- FCLK_CLK0 → DMA aclk, NN ap_clk
- Reset → DMA aresetn, NN ap_rst_n  
- Zynq M_AXI_GP0 → AXI Interconnect → DMA S_AXI_LITE
- DMA M_AXI_MM2S + S_AXI_S2MM → AXI Interconnect → Zynq S_AXI_HP0

---

## Step 8 — Manual AXI-Stream connections

These two must be wired by hand (hover until pencil cursor, drag):

```
AXI DMA  M_AXIS_MM2S    →   myproject_axi  in_stream
myproject_axi  out_stream  →   AXI DMA  S_AXIS_S2MM
```

---

## Step 9 — Validate

Ctrl+Shift+V → expect "Validation successful"  
`ap_ctrl` unconnected warning is safe — ignore it.

---

## Step 10 — Generate bitstream

Sources → right-click design_1.bd → Generate HDL Wrapper →  
Let Vivado manage → OK

Flow Navigator → Generate Bitstream → Yes → OK  
Wait ~35 minutes.

---

## Step 11 — Collect output files

```
autoencoder_pynq\autoencoder_pynq.runs\impl_1\design_1_wrapper.bit  →  autoencoder.bit
autoencoder_pynq\autoencoder_pynq.gen\sources_1\bd\design_1\hw_handoff\design_1.hwh  →  autoencoder.hwh
```
