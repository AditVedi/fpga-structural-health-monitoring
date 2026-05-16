#ifndef MYPROJECT_H_
#define MYPROJECT_H_

#include "ap_fixed.h"
#include "ap_int.h"
#include "hls_stream.h"

#include "defines.h"


// Prototype of top level function for C-synthesis
void myproject(
    hls::stream<input_t> &input_layer,
    hls::stream<result_t> &layer12_out
);

// hls-fpga-machine-learning insert emulator-defines



// ============================================================================
// AXI wrapper declaration
// ============================================================================

#include "ap_axi_sdata.h"

typedef ap_axiu<8,0,0,0> axi_word_t;

void myproject_axi(
    hls::stream<axi_word_t> &in_stream,
    hls::stream<axi_word_t> &out_stream
);


#endif
