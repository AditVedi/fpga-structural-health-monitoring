#ifndef DEFINES_H_
#define DEFINES_H_

#include "ap_fixed.h"
#include "ap_int.h"
#include "nnet_utils/nnet_types.h"
#include <array>
#include <cstddef>
#include <cstdio>
#include <tuple>
#include <tuple>


// hls-fpga-machine-learning insert numbers

// hls-fpga-machine-learning insert layer-precision
typedef nnet::array<ap_fixed<8,4>, 128*1> input_t;
typedef ap_fixed<8,4> enc1_accum_t;
typedef nnet::array<ap_fixed<8,4>, 64*1> layer2_t;
typedef ap_fixed<8,4> enc1_weight_t;
typedef ap_fixed<8,4> enc1_bias_t;
typedef ap_uint<1> layer2_index;
typedef nnet::array<ap_fixed<8,4>, 64*1> layer3_t;
typedef ap_fixed<18,8> enc1_relu_table_t;
typedef ap_fixed<8,4> enc2_accum_t;
typedef nnet::array<ap_fixed<8,4>, 32*1> layer4_t;
typedef ap_fixed<8,4> enc2_weight_t;
typedef ap_fixed<8,4> enc2_bias_t;
typedef ap_uint<1> layer4_index;
typedef nnet::array<ap_fixed<8,4>, 32*1> layer5_t;
typedef ap_fixed<18,8> enc2_relu_table_t;
typedef ap_fixed<8,4> bottleneck_accum_t;
typedef nnet::array<ap_fixed<8,4>, 32*1> layer6_t;
typedef ap_fixed<8,4> bottleneck_weight_t;
typedef ap_fixed<8,4> bottleneck_bias_t;
typedef ap_uint<1> layer6_index;
typedef nnet::array<ap_fixed<8,4>, 32*1> layer7_t;
typedef ap_fixed<18,8> bottleneck_relu_table_t;
typedef ap_fixed<8,4> dec1_accum_t;
typedef nnet::array<ap_fixed<8,4>, 32*1> layer8_t;
typedef ap_fixed<8,4> dec1_weight_t;
typedef ap_fixed<8,4> dec1_bias_t;
typedef ap_uint<1> layer8_index;
typedef nnet::array<ap_fixed<8,4>, 32*1> layer9_t;
typedef ap_fixed<18,8> dec1_relu_table_t;
typedef ap_fixed<8,4> dec2_accum_t;
typedef nnet::array<ap_fixed<8,4>, 64*1> layer10_t;
typedef ap_fixed<8,4> dec2_weight_t;
typedef ap_fixed<8,4> dec2_bias_t;
typedef ap_uint<1> layer10_index;
typedef nnet::array<ap_fixed<8,4>, 64*1> layer11_t;
typedef ap_fixed<18,8> dec2_relu_table_t;
typedef ap_fixed<8,4> output_accum_t;
typedef nnet::array<ap_fixed<8,4>, 128*1> result_t;
typedef ap_fixed<8,4> output_weight_t;
typedef ap_fixed<8,4> output_bias_t;
typedef ap_uint<1> layer12_index;

// hls-fpga-machine-learning insert emulator-defines


#endif
