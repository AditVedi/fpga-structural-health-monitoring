#include <iostream>

#include "myproject.h"
#include "parameters.h"


// ============================================================================
// DMA-compatible AXI-stream wrapper with TLAST
// ============================================================================

#include "ap_axi_sdata.h"

typedef ap_axiu<8,0,0,0> axi_word_t;

void myproject_axi(
    hls::stream<axi_word_t> &in_stream,
    hls::stream<axi_word_t> &out_stream
)
{
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

    for (int i = 0; i < 128; i++) {
#pragma HLS PIPELINE II=1

        axi_word_t beat = in_stream.read();

        in_vec[i] = *reinterpret_cast<input_t::value_type*>(&beat.data);
    }

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
    for (int i = 0; i < 128; i++) {
#pragma HLS PIPELINE II=1

        axi_word_t beat;

        beat.data = *reinterpret_cast<ap_uint<8>*>(&out_vec[i]);

        beat.keep = 1;
        beat.strb = 1;
        beat.last = (i == 128 - 1);

        out_stream.write(beat);
    }
}

// ============================================================================
// End AXI wrapper
// ============================================================================




void myproject(
    hls::stream<input_t> &input_layer,
    hls::stream<result_t> &layer12_out
) {

    // hls-fpga-machine-learning insert IO
    #pragma HLS INTERFACE axis port=input_layer,layer12_out 
    #pragma HLS DATAFLOW

    // hls-fpga-machine-learning insert load weights
#ifndef __SYNTHESIS__
    static bool loaded_weights = false;
    if (!loaded_weights) {
        nnet::load_weights_from_txt<enc1_weight_t, 8192>(w2, "w2.txt");
        nnet::load_weights_from_txt<enc1_bias_t, 64>(b2, "b2.txt");
        nnet::load_weights_from_txt<enc2_weight_t, 2048>(w4, "w4.txt");
        nnet::load_weights_from_txt<enc2_bias_t, 32>(b4, "b4.txt");
        nnet::load_weights_from_txt<bottleneck_weight_t, 1024>(w6, "w6.txt");
        nnet::load_weights_from_txt<bottleneck_bias_t, 32>(b6, "b6.txt");
        nnet::load_weights_from_txt<dec1_weight_t, 1024>(w8, "w8.txt");
        nnet::load_weights_from_txt<dec1_bias_t, 32>(b8, "b8.txt");
        nnet::load_weights_from_txt<dec2_weight_t, 2048>(w10, "w10.txt");
        nnet::load_weights_from_txt<dec2_bias_t, 64>(b10, "b10.txt");
        nnet::load_weights_from_txt<output_weight_t, 8192>(w12, "w12.txt");
        nnet::load_weights_from_txt<output_bias_t, 128>(b12, "b12.txt");
        loaded_weights = true;    }
#endif
    // ****************************************
    // NETWORK INSTANTIATION
    // ****************************************

    // hls-fpga-machine-learning insert layers

    hls::stream<layer2_t> layer2_out("layer2_out");
    #pragma HLS STREAM variable=layer2_out depth=1

    hls::stream<layer3_t> layer3_out("layer3_out");
    #pragma HLS STREAM variable=layer3_out depth=1

    hls::stream<layer4_t> layer4_out("layer4_out");
    #pragma HLS STREAM variable=layer4_out depth=1

    hls::stream<layer5_t> layer5_out("layer5_out");
    #pragma HLS STREAM variable=layer5_out depth=1

    hls::stream<layer6_t> layer6_out("layer6_out");
    #pragma HLS STREAM variable=layer6_out depth=1

    hls::stream<layer7_t> layer7_out("layer7_out");
    #pragma HLS STREAM variable=layer7_out depth=1

    hls::stream<layer8_t> layer8_out("layer8_out");
    #pragma HLS STREAM variable=layer8_out depth=1

    hls::stream<layer9_t> layer9_out("layer9_out");
    #pragma HLS STREAM variable=layer9_out depth=1

    hls::stream<layer10_t> layer10_out("layer10_out");
    #pragma HLS STREAM variable=layer10_out depth=1

    hls::stream<layer11_t> layer11_out("layer11_out");
    #pragma HLS STREAM variable=layer11_out depth=1

    nnet::dense<input_t, layer2_t, config2>(input_layer, layer2_out, w2, b2); // enc1

    nnet::relu<layer2_t, layer3_t, relu_config3>(layer2_out, layer3_out); // enc1_relu

    nnet::dense<layer3_t, layer4_t, config4>(layer3_out, layer4_out, w4, b4); // enc2

    nnet::relu<layer4_t, layer5_t, relu_config5>(layer4_out, layer5_out); // enc2_relu

    nnet::dense<layer5_t, layer6_t, config6>(layer5_out, layer6_out, w6, b6); // bottleneck

    nnet::relu<layer6_t, layer7_t, relu_config7>(layer6_out, layer7_out); // bottleneck_relu

    nnet::dense<layer7_t, layer8_t, config8>(layer7_out, layer8_out, w8, b8); // dec1

    nnet::relu<layer8_t, layer9_t, relu_config9>(layer8_out, layer9_out); // dec1_relu

    nnet::dense<layer9_t, layer10_t, config10>(layer9_out, layer10_out, w10, b10); // dec2

    nnet::relu<layer10_t, layer11_t, relu_config11>(layer10_out, layer11_out); // dec2_relu

    nnet::dense<layer11_t, result_t, config12>(layer11_out, layer12_out, w12, b12); // output

}

