// (c) Copyright 1995-2018 Xilinx, Inc. All rights reserved.
// 
// This file contains confidential and proprietary information
// of Xilinx, Inc. and is protected under U.S. and
// international copyright and other intellectual property
// laws.
// 
// DISCLAIMER
// This disclaimer is not a license and does not grant any
// rights to the materials distributed herewith. Except as
// otherwise provided in a valid license issued to you by
// Xilinx, and to the maximum extent permitted by applicable
// law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
// WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES
// AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
// BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
// INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
// (2) Xilinx shall not be liable (whether in contract or tort,
// including negligence, or under any other theory of
// liability) for any loss or damage of any kind or nature
// related to, arising under or in connection with these
// materials, including for any direct, or any indirect,
// special, incidental, or consequential loss or damage
// (including loss of data, profits, goodwill, or any type of
// loss or damage suffered as a result of any action brought
// by a third party) even if such damage or loss was
// reasonably foreseeable or Xilinx had been advised of the
// possibility of the same.
// 
// CRITICAL APPLICATIONS
// Xilinx products are not designed or intended to be fail-
// safe, or for use in any application requiring fail-safe
// performance, such as life-support or safety devices or
// systems, Class III medical devices, nuclear facilities,
// applications related to the deployment of airbags, or any
// other applications that could lead to death, personal
// injury, or severe property or environmental damage
// (individually and collectively, "Critical
// Applications"). Customer assumes the sole risk and
// liability of any use of Xilinx products in Critical
// Applications, subject only to applicable laws and
// regulations governing limitations on product liability.
// 
// THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
// PART OF THIS FILE AT ALL TIMES.
// 
// DO NOT MODIFY THIS FILE.

// IP VLNV: xilinx.com:ip:cmac_usplus:2.4
// IP Revision: 1

// The following must be inserted into your Verilog file for this
// core to be instantiated. Change the instance name and port connections
// (in parentheses) to your own signal names.

//----------- Begin Cut here for INSTANTIATION Template ---// INST_TAG
cmac_usplus_0 your_instance_name (
  .txdata_in(txdata_in),                                                        // output wire [511 : 0] txdata_in
  .txctrl0_in(txctrl0_in),                                                      // output wire [63 : 0] txctrl0_in
  .txctrl1_in(txctrl1_in),                                                      // output wire [63 : 0] txctrl1_in
  .rxdata_out(rxdata_out),                                                      // input wire [511 : 0] rxdata_out
  .rxctrl0_out(rxctrl0_out),                                                    // input wire [63 : 0] rxctrl0_out
  .rxctrl1_out(rxctrl1_out),                                                    // input wire [63 : 0] rxctrl1_out
  .ctl_tx_rsfec_enable(ctl_tx_rsfec_enable),                                    // input wire ctl_tx_rsfec_enable
  .ctl_rx_rsfec_enable(ctl_rx_rsfec_enable),                                    // input wire ctl_rx_rsfec_enable
  .ctl_rsfec_ieee_error_indication_mode(ctl_rsfec_ieee_error_indication_mode),  // input wire ctl_rsfec_ieee_error_indication_mode
  .ctl_rx_rsfec_enable_correction(ctl_rx_rsfec_enable_correction),              // input wire ctl_rx_rsfec_enable_correction
  .ctl_rx_rsfec_enable_indication(ctl_rx_rsfec_enable_indication),              // input wire ctl_rx_rsfec_enable_indication
  .stat_rx_rsfec_am_lock0(stat_rx_rsfec_am_lock0),                              // output wire stat_rx_rsfec_am_lock0
  .stat_rx_rsfec_am_lock1(stat_rx_rsfec_am_lock1),                              // output wire stat_rx_rsfec_am_lock1
  .stat_rx_rsfec_am_lock2(stat_rx_rsfec_am_lock2),                              // output wire stat_rx_rsfec_am_lock2
  .stat_rx_rsfec_am_lock3(stat_rx_rsfec_am_lock3),                              // output wire stat_rx_rsfec_am_lock3
  .stat_rx_rsfec_corrected_cw_inc(stat_rx_rsfec_corrected_cw_inc),              // output wire stat_rx_rsfec_corrected_cw_inc
  .stat_rx_rsfec_cw_inc(stat_rx_rsfec_cw_inc),                                  // output wire stat_rx_rsfec_cw_inc
  .stat_rx_rsfec_err_count0_inc(stat_rx_rsfec_err_count0_inc),                  // output wire [2 : 0] stat_rx_rsfec_err_count0_inc
  .stat_rx_rsfec_err_count1_inc(stat_rx_rsfec_err_count1_inc),                  // output wire [2 : 0] stat_rx_rsfec_err_count1_inc
  .stat_rx_rsfec_err_count2_inc(stat_rx_rsfec_err_count2_inc),                  // output wire [2 : 0] stat_rx_rsfec_err_count2_inc
  .stat_rx_rsfec_err_count3_inc(stat_rx_rsfec_err_count3_inc),                  // output wire [2 : 0] stat_rx_rsfec_err_count3_inc
  .stat_rx_rsfec_hi_ser(stat_rx_rsfec_hi_ser),                                  // output wire stat_rx_rsfec_hi_ser
  .stat_rx_rsfec_lane_alignment_status(stat_rx_rsfec_lane_alignment_status),    // output wire stat_rx_rsfec_lane_alignment_status
  .stat_rx_rsfec_lane_fill_0(stat_rx_rsfec_lane_fill_0),                        // output wire [13 : 0] stat_rx_rsfec_lane_fill_0
  .stat_rx_rsfec_lane_fill_1(stat_rx_rsfec_lane_fill_1),                        // output wire [13 : 0] stat_rx_rsfec_lane_fill_1
  .stat_rx_rsfec_lane_fill_2(stat_rx_rsfec_lane_fill_2),                        // output wire [13 : 0] stat_rx_rsfec_lane_fill_2
  .stat_rx_rsfec_lane_fill_3(stat_rx_rsfec_lane_fill_3),                        // output wire [13 : 0] stat_rx_rsfec_lane_fill_3
  .stat_rx_rsfec_lane_mapping(stat_rx_rsfec_lane_mapping),                      // output wire [7 : 0] stat_rx_rsfec_lane_mapping
  .stat_rx_rsfec_uncorrected_cw_inc(stat_rx_rsfec_uncorrected_cw_inc),          // output wire stat_rx_rsfec_uncorrected_cw_inc
  .rx_dataout0(rx_dataout0),                                                    // output wire [127 : 0] rx_dataout0
  .rx_dataout1(rx_dataout1),                                                    // output wire [127 : 0] rx_dataout1
  .rx_dataout2(rx_dataout2),                                                    // output wire [127 : 0] rx_dataout2
  .rx_dataout3(rx_dataout3),                                                    // output wire [127 : 0] rx_dataout3
  .rx_enaout0(rx_enaout0),                                                      // output wire rx_enaout0
  .rx_enaout1(rx_enaout1),                                                      // output wire rx_enaout1
  .rx_enaout2(rx_enaout2),                                                      // output wire rx_enaout2
  .rx_enaout3(rx_enaout3),                                                      // output wire rx_enaout3
  .rx_eopout0(rx_eopout0),                                                      // output wire rx_eopout0
  .rx_eopout1(rx_eopout1),                                                      // output wire rx_eopout1
  .rx_eopout2(rx_eopout2),                                                      // output wire rx_eopout2
  .rx_eopout3(rx_eopout3),                                                      // output wire rx_eopout3
  .rx_errout0(rx_errout0),                                                      // output wire rx_errout0
  .rx_errout1(rx_errout1),                                                      // output wire rx_errout1
  .rx_errout2(rx_errout2),                                                      // output wire rx_errout2
  .rx_errout3(rx_errout3),                                                      // output wire rx_errout3
  .rx_mtyout0(rx_mtyout0),                                                      // output wire [3 : 0] rx_mtyout0
  .rx_mtyout1(rx_mtyout1),                                                      // output wire [3 : 0] rx_mtyout1
  .rx_mtyout2(rx_mtyout2),                                                      // output wire [3 : 0] rx_mtyout2
  .rx_mtyout3(rx_mtyout3),                                                      // output wire [3 : 0] rx_mtyout3
  .rx_sopout0(rx_sopout0),                                                      // output wire rx_sopout0
  .rx_sopout1(rx_sopout1),                                                      // output wire rx_sopout1
  .rx_sopout2(rx_sopout2),                                                      // output wire rx_sopout2
  .rx_sopout3(rx_sopout3),                                                      // output wire rx_sopout3
  .rx_otn_bip8_0(rx_otn_bip8_0),                                                // output wire [7 : 0] rx_otn_bip8_0
  .rx_otn_bip8_1(rx_otn_bip8_1),                                                // output wire [7 : 0] rx_otn_bip8_1
  .rx_otn_bip8_2(rx_otn_bip8_2),                                                // output wire [7 : 0] rx_otn_bip8_2
  .rx_otn_bip8_3(rx_otn_bip8_3),                                                // output wire [7 : 0] rx_otn_bip8_3
  .rx_otn_bip8_4(rx_otn_bip8_4),                                                // output wire [7 : 0] rx_otn_bip8_4
  .rx_otn_data_0(rx_otn_data_0),                                                // output wire [65 : 0] rx_otn_data_0
  .rx_otn_data_1(rx_otn_data_1),                                                // output wire [65 : 0] rx_otn_data_1
  .rx_otn_data_2(rx_otn_data_2),                                                // output wire [65 : 0] rx_otn_data_2
  .rx_otn_data_3(rx_otn_data_3),                                                // output wire [65 : 0] rx_otn_data_3
  .rx_otn_data_4(rx_otn_data_4),                                                // output wire [65 : 0] rx_otn_data_4
  .rx_otn_ena(rx_otn_ena),                                                      // output wire rx_otn_ena
  .rx_otn_lane0(rx_otn_lane0),                                                  // output wire rx_otn_lane0
  .rx_otn_vlmarker(rx_otn_vlmarker),                                            // output wire rx_otn_vlmarker
  .rx_preambleout(rx_preambleout),                                              // output wire [55 : 0] rx_preambleout
  .stat_rx_aligned(stat_rx_aligned),                                            // output wire stat_rx_aligned
  .stat_rx_aligned_err(stat_rx_aligned_err),                                    // output wire stat_rx_aligned_err
  .stat_rx_bad_code(stat_rx_bad_code),                                          // output wire [2 : 0] stat_rx_bad_code
  .stat_rx_bad_fcs(stat_rx_bad_fcs),                                            // output wire [2 : 0] stat_rx_bad_fcs
  .stat_rx_bad_preamble(stat_rx_bad_preamble),                                  // output wire stat_rx_bad_preamble
  .stat_rx_bad_sfd(stat_rx_bad_sfd),                                            // output wire stat_rx_bad_sfd
  .stat_rx_bip_err_0(stat_rx_bip_err_0),                                        // output wire stat_rx_bip_err_0
  .stat_rx_bip_err_1(stat_rx_bip_err_1),                                        // output wire stat_rx_bip_err_1
  .stat_rx_bip_err_10(stat_rx_bip_err_10),                                      // output wire stat_rx_bip_err_10
  .stat_rx_bip_err_11(stat_rx_bip_err_11),                                      // output wire stat_rx_bip_err_11
  .stat_rx_bip_err_12(stat_rx_bip_err_12),                                      // output wire stat_rx_bip_err_12
  .stat_rx_bip_err_13(stat_rx_bip_err_13),                                      // output wire stat_rx_bip_err_13
  .stat_rx_bip_err_14(stat_rx_bip_err_14),                                      // output wire stat_rx_bip_err_14
  .stat_rx_bip_err_15(stat_rx_bip_err_15),                                      // output wire stat_rx_bip_err_15
  .stat_rx_bip_err_16(stat_rx_bip_err_16),                                      // output wire stat_rx_bip_err_16
  .stat_rx_bip_err_17(stat_rx_bip_err_17),                                      // output wire stat_rx_bip_err_17
  .stat_rx_bip_err_18(stat_rx_bip_err_18),                                      // output wire stat_rx_bip_err_18
  .stat_rx_bip_err_19(stat_rx_bip_err_19),                                      // output wire stat_rx_bip_err_19
  .stat_rx_bip_err_2(stat_rx_bip_err_2),                                        // output wire stat_rx_bip_err_2
  .stat_rx_bip_err_3(stat_rx_bip_err_3),                                        // output wire stat_rx_bip_err_3
  .stat_rx_bip_err_4(stat_rx_bip_err_4),                                        // output wire stat_rx_bip_err_4
  .stat_rx_bip_err_5(stat_rx_bip_err_5),                                        // output wire stat_rx_bip_err_5
  .stat_rx_bip_err_6(stat_rx_bip_err_6),                                        // output wire stat_rx_bip_err_6
  .stat_rx_bip_err_7(stat_rx_bip_err_7),                                        // output wire stat_rx_bip_err_7
  .stat_rx_bip_err_8(stat_rx_bip_err_8),                                        // output wire stat_rx_bip_err_8
  .stat_rx_bip_err_9(stat_rx_bip_err_9),                                        // output wire stat_rx_bip_err_9
  .stat_rx_block_lock(stat_rx_block_lock),                                      // output wire [19 : 0] stat_rx_block_lock
  .stat_rx_broadcast(stat_rx_broadcast),                                        // output wire stat_rx_broadcast
  .stat_rx_fragment(stat_rx_fragment),                                          // output wire [2 : 0] stat_rx_fragment
  .stat_rx_framing_err_0(stat_rx_framing_err_0),                                // output wire [1 : 0] stat_rx_framing_err_0
  .stat_rx_framing_err_1(stat_rx_framing_err_1),                                // output wire [1 : 0] stat_rx_framing_err_1
  .stat_rx_framing_err_10(stat_rx_framing_err_10),                              // output wire [1 : 0] stat_rx_framing_err_10
  .stat_rx_framing_err_11(stat_rx_framing_err_11),                              // output wire [1 : 0] stat_rx_framing_err_11
  .stat_rx_framing_err_12(stat_rx_framing_err_12),                              // output wire [1 : 0] stat_rx_framing_err_12
  .stat_rx_framing_err_13(stat_rx_framing_err_13),                              // output wire [1 : 0] stat_rx_framing_err_13
  .stat_rx_framing_err_14(stat_rx_framing_err_14),                              // output wire [1 : 0] stat_rx_framing_err_14
  .stat_rx_framing_err_15(stat_rx_framing_err_15),                              // output wire [1 : 0] stat_rx_framing_err_15
  .stat_rx_framing_err_16(stat_rx_framing_err_16),                              // output wire [1 : 0] stat_rx_framing_err_16
  .stat_rx_framing_err_17(stat_rx_framing_err_17),                              // output wire [1 : 0] stat_rx_framing_err_17
  .stat_rx_framing_err_18(stat_rx_framing_err_18),                              // output wire [1 : 0] stat_rx_framing_err_18
  .stat_rx_framing_err_19(stat_rx_framing_err_19),                              // output wire [1 : 0] stat_rx_framing_err_19
  .stat_rx_framing_err_2(stat_rx_framing_err_2),                                // output wire [1 : 0] stat_rx_framing_err_2
  .stat_rx_framing_err_3(stat_rx_framing_err_3),                                // output wire [1 : 0] stat_rx_framing_err_3
  .stat_rx_framing_err_4(stat_rx_framing_err_4),                                // output wire [1 : 0] stat_rx_framing_err_4
  .stat_rx_framing_err_5(stat_rx_framing_err_5),                                // output wire [1 : 0] stat_rx_framing_err_5
  .stat_rx_framing_err_6(stat_rx_framing_err_6),                                // output wire [1 : 0] stat_rx_framing_err_6
  .stat_rx_framing_err_7(stat_rx_framing_err_7),                                // output wire [1 : 0] stat_rx_framing_err_7
  .stat_rx_framing_err_8(stat_rx_framing_err_8),                                // output wire [1 : 0] stat_rx_framing_err_8
  .stat_rx_framing_err_9(stat_rx_framing_err_9),                                // output wire [1 : 0] stat_rx_framing_err_9
  .stat_rx_framing_err_valid_0(stat_rx_framing_err_valid_0),                    // output wire stat_rx_framing_err_valid_0
  .stat_rx_framing_err_valid_1(stat_rx_framing_err_valid_1),                    // output wire stat_rx_framing_err_valid_1
  .stat_rx_framing_err_valid_10(stat_rx_framing_err_valid_10),                  // output wire stat_rx_framing_err_valid_10
  .stat_rx_framing_err_valid_11(stat_rx_framing_err_valid_11),                  // output wire stat_rx_framing_err_valid_11
  .stat_rx_framing_err_valid_12(stat_rx_framing_err_valid_12),                  // output wire stat_rx_framing_err_valid_12
  .stat_rx_framing_err_valid_13(stat_rx_framing_err_valid_13),                  // output wire stat_rx_framing_err_valid_13
  .stat_rx_framing_err_valid_14(stat_rx_framing_err_valid_14),                  // output wire stat_rx_framing_err_valid_14
  .stat_rx_framing_err_valid_15(stat_rx_framing_err_valid_15),                  // output wire stat_rx_framing_err_valid_15
  .stat_rx_framing_err_valid_16(stat_rx_framing_err_valid_16),                  // output wire stat_rx_framing_err_valid_16
  .stat_rx_framing_err_valid_17(stat_rx_framing_err_valid_17),                  // output wire stat_rx_framing_err_valid_17
  .stat_rx_framing_err_valid_18(stat_rx_framing_err_valid_18),                  // output wire stat_rx_framing_err_valid_18
  .stat_rx_framing_err_valid_19(stat_rx_framing_err_valid_19),                  // output wire stat_rx_framing_err_valid_19
  .stat_rx_framing_err_valid_2(stat_rx_framing_err_valid_2),                    // output wire stat_rx_framing_err_valid_2
  .stat_rx_framing_err_valid_3(stat_rx_framing_err_valid_3),                    // output wire stat_rx_framing_err_valid_3
  .stat_rx_framing_err_valid_4(stat_rx_framing_err_valid_4),                    // output wire stat_rx_framing_err_valid_4
  .stat_rx_framing_err_valid_5(stat_rx_framing_err_valid_5),                    // output wire stat_rx_framing_err_valid_5
  .stat_rx_framing_err_valid_6(stat_rx_framing_err_valid_6),                    // output wire stat_rx_framing_err_valid_6
  .stat_rx_framing_err_valid_7(stat_rx_framing_err_valid_7),                    // output wire stat_rx_framing_err_valid_7
  .stat_rx_framing_err_valid_8(stat_rx_framing_err_valid_8),                    // output wire stat_rx_framing_err_valid_8
  .stat_rx_framing_err_valid_9(stat_rx_framing_err_valid_9),                    // output wire stat_rx_framing_err_valid_9
  .stat_rx_got_signal_os(stat_rx_got_signal_os),                                // output wire stat_rx_got_signal_os
  .stat_rx_hi_ber(stat_rx_hi_ber),                                              // output wire stat_rx_hi_ber
  .stat_rx_inrangeerr(stat_rx_inrangeerr),                                      // output wire stat_rx_inrangeerr
  .stat_rx_internal_local_fault(stat_rx_internal_local_fault),                  // output wire stat_rx_internal_local_fault
  .stat_rx_jabber(stat_rx_jabber),                                              // output wire stat_rx_jabber
  .stat_rx_local_fault(stat_rx_local_fault),                                    // output wire stat_rx_local_fault
  .stat_rx_mf_err(stat_rx_mf_err),                                              // output wire [19 : 0] stat_rx_mf_err
  .stat_rx_mf_len_err(stat_rx_mf_len_err),                                      // output wire [19 : 0] stat_rx_mf_len_err
  .stat_rx_mf_repeat_err(stat_rx_mf_repeat_err),                                // output wire [19 : 0] stat_rx_mf_repeat_err
  .stat_rx_misaligned(stat_rx_misaligned),                                      // output wire stat_rx_misaligned
  .stat_rx_multicast(stat_rx_multicast),                                        // output wire stat_rx_multicast
  .stat_rx_oversize(stat_rx_oversize),                                          // output wire stat_rx_oversize
  .stat_rx_packet_1024_1518_bytes(stat_rx_packet_1024_1518_bytes),              // output wire stat_rx_packet_1024_1518_bytes
  .stat_rx_packet_128_255_bytes(stat_rx_packet_128_255_bytes),                  // output wire stat_rx_packet_128_255_bytes
  .stat_rx_packet_1519_1522_bytes(stat_rx_packet_1519_1522_bytes),              // output wire stat_rx_packet_1519_1522_bytes
  .stat_rx_packet_1523_1548_bytes(stat_rx_packet_1523_1548_bytes),              // output wire stat_rx_packet_1523_1548_bytes
  .stat_rx_packet_1549_2047_bytes(stat_rx_packet_1549_2047_bytes),              // output wire stat_rx_packet_1549_2047_bytes
  .stat_rx_packet_2048_4095_bytes(stat_rx_packet_2048_4095_bytes),              // output wire stat_rx_packet_2048_4095_bytes
  .stat_rx_packet_256_511_bytes(stat_rx_packet_256_511_bytes),                  // output wire stat_rx_packet_256_511_bytes
  .stat_rx_packet_4096_8191_bytes(stat_rx_packet_4096_8191_bytes),              // output wire stat_rx_packet_4096_8191_bytes
  .stat_rx_packet_512_1023_bytes(stat_rx_packet_512_1023_bytes),                // output wire stat_rx_packet_512_1023_bytes
  .stat_rx_packet_64_bytes(stat_rx_packet_64_bytes),                            // output wire stat_rx_packet_64_bytes
  .stat_rx_packet_65_127_bytes(stat_rx_packet_65_127_bytes),                    // output wire stat_rx_packet_65_127_bytes
  .stat_rx_packet_8192_9215_bytes(stat_rx_packet_8192_9215_bytes),              // output wire stat_rx_packet_8192_9215_bytes
  .stat_rx_packet_bad_fcs(stat_rx_packet_bad_fcs),                              // output wire stat_rx_packet_bad_fcs
  .stat_rx_packet_large(stat_rx_packet_large),                                  // output wire stat_rx_packet_large
  .stat_rx_packet_small(stat_rx_packet_small),                                  // output wire [2 : 0] stat_rx_packet_small
  .stat_rx_pause(stat_rx_pause),                                                // output wire stat_rx_pause
  .stat_rx_pause_quanta0(stat_rx_pause_quanta0),                                // output wire [15 : 0] stat_rx_pause_quanta0
  .stat_rx_pause_quanta1(stat_rx_pause_quanta1),                                // output wire [15 : 0] stat_rx_pause_quanta1
  .stat_rx_pause_quanta2(stat_rx_pause_quanta2),                                // output wire [15 : 0] stat_rx_pause_quanta2
  .stat_rx_pause_quanta3(stat_rx_pause_quanta3),                                // output wire [15 : 0] stat_rx_pause_quanta3
  .stat_rx_pause_quanta4(stat_rx_pause_quanta4),                                // output wire [15 : 0] stat_rx_pause_quanta4
  .stat_rx_pause_quanta5(stat_rx_pause_quanta5),                                // output wire [15 : 0] stat_rx_pause_quanta5
  .stat_rx_pause_quanta6(stat_rx_pause_quanta6),                                // output wire [15 : 0] stat_rx_pause_quanta6
  .stat_rx_pause_quanta7(stat_rx_pause_quanta7),                                // output wire [15 : 0] stat_rx_pause_quanta7
  .stat_rx_pause_quanta8(stat_rx_pause_quanta8),                                // output wire [15 : 0] stat_rx_pause_quanta8
  .stat_rx_pause_req(stat_rx_pause_req),                                        // output wire [8 : 0] stat_rx_pause_req
  .stat_rx_pause_valid(stat_rx_pause_valid),                                    // output wire [8 : 0] stat_rx_pause_valid
  .stat_rx_user_pause(stat_rx_user_pause),                                      // output wire stat_rx_user_pause
  .ctl_rx_check_etype_gcp(ctl_rx_check_etype_gcp),                              // input wire ctl_rx_check_etype_gcp
  .ctl_rx_check_etype_gpp(ctl_rx_check_etype_gpp),                              // input wire ctl_rx_check_etype_gpp
  .ctl_rx_check_etype_pcp(ctl_rx_check_etype_pcp),                              // input wire ctl_rx_check_etype_pcp
  .ctl_rx_check_etype_ppp(ctl_rx_check_etype_ppp),                              // input wire ctl_rx_check_etype_ppp
  .ctl_rx_check_mcast_gcp(ctl_rx_check_mcast_gcp),                              // input wire ctl_rx_check_mcast_gcp
  .ctl_rx_check_mcast_gpp(ctl_rx_check_mcast_gpp),                              // input wire ctl_rx_check_mcast_gpp
  .ctl_rx_check_mcast_pcp(ctl_rx_check_mcast_pcp),                              // input wire ctl_rx_check_mcast_pcp
  .ctl_rx_check_mcast_ppp(ctl_rx_check_mcast_ppp),                              // input wire ctl_rx_check_mcast_ppp
  .ctl_rx_check_opcode_gcp(ctl_rx_check_opcode_gcp),                            // input wire ctl_rx_check_opcode_gcp
  .ctl_rx_check_opcode_gpp(ctl_rx_check_opcode_gpp),                            // input wire ctl_rx_check_opcode_gpp
  .ctl_rx_check_opcode_pcp(ctl_rx_check_opcode_pcp),                            // input wire ctl_rx_check_opcode_pcp
  .ctl_rx_check_opcode_ppp(ctl_rx_check_opcode_ppp),                            // input wire ctl_rx_check_opcode_ppp
  .ctl_rx_check_sa_gcp(ctl_rx_check_sa_gcp),                                    // input wire ctl_rx_check_sa_gcp
  .ctl_rx_check_sa_gpp(ctl_rx_check_sa_gpp),                                    // input wire ctl_rx_check_sa_gpp
  .ctl_rx_check_sa_pcp(ctl_rx_check_sa_pcp),                                    // input wire ctl_rx_check_sa_pcp
  .ctl_rx_check_sa_ppp(ctl_rx_check_sa_ppp),                                    // input wire ctl_rx_check_sa_ppp
  .ctl_rx_check_ucast_gcp(ctl_rx_check_ucast_gcp),                              // input wire ctl_rx_check_ucast_gcp
  .ctl_rx_check_ucast_gpp(ctl_rx_check_ucast_gpp),                              // input wire ctl_rx_check_ucast_gpp
  .ctl_rx_check_ucast_pcp(ctl_rx_check_ucast_pcp),                              // input wire ctl_rx_check_ucast_pcp
  .ctl_rx_check_ucast_ppp(ctl_rx_check_ucast_ppp),                              // input wire ctl_rx_check_ucast_ppp
  .ctl_rx_enable_gcp(ctl_rx_enable_gcp),                                        // input wire ctl_rx_enable_gcp
  .ctl_rx_enable_gpp(ctl_rx_enable_gpp),                                        // input wire ctl_rx_enable_gpp
  .ctl_rx_enable_pcp(ctl_rx_enable_pcp),                                        // input wire ctl_rx_enable_pcp
  .ctl_rx_enable_ppp(ctl_rx_enable_ppp),                                        // input wire ctl_rx_enable_ppp
  .ctl_rx_pause_ack(ctl_rx_pause_ack),                                          // input wire [8 : 0] ctl_rx_pause_ack
  .ctl_rx_pause_enable(ctl_rx_pause_enable),                                    // input wire [8 : 0] ctl_rx_pause_enable
  .ctl_rx_enable(ctl_rx_enable),                                                // input wire ctl_rx_enable
  .ctl_rx_force_resync(ctl_rx_force_resync),                                    // input wire ctl_rx_force_resync
  .ctl_rx_test_pattern(ctl_rx_test_pattern),                                    // input wire ctl_rx_test_pattern
  .rx_clk(rx_clk),                                                              // input wire rx_clk
  .stat_rx_received_local_fault(stat_rx_received_local_fault),                  // output wire stat_rx_received_local_fault
  .stat_rx_remote_fault(stat_rx_remote_fault),                                  // output wire stat_rx_remote_fault
  .stat_rx_status(stat_rx_status),                                              // output wire stat_rx_status
  .stat_rx_stomped_fcs(stat_rx_stomped_fcs),                                    // output wire [2 : 0] stat_rx_stomped_fcs
  .stat_rx_synced(stat_rx_synced),                                              // output wire [19 : 0] stat_rx_synced
  .stat_rx_synced_err(stat_rx_synced_err),                                      // output wire [19 : 0] stat_rx_synced_err
  .stat_rx_test_pattern_mismatch(stat_rx_test_pattern_mismatch),                // output wire [2 : 0] stat_rx_test_pattern_mismatch
  .stat_rx_toolong(stat_rx_toolong),                                            // output wire stat_rx_toolong
  .stat_rx_total_bytes(stat_rx_total_bytes),                                    // output wire [6 : 0] stat_rx_total_bytes
  .stat_rx_total_good_bytes(stat_rx_total_good_bytes),                          // output wire [13 : 0] stat_rx_total_good_bytes
  .stat_rx_total_good_packets(stat_rx_total_good_packets),                      // output wire stat_rx_total_good_packets
  .stat_rx_total_packets(stat_rx_total_packets),                                // output wire [2 : 0] stat_rx_total_packets
  .stat_rx_truncated(stat_rx_truncated),                                        // output wire stat_rx_truncated
  .stat_rx_undersize(stat_rx_undersize),                                        // output wire [2 : 0] stat_rx_undersize
  .stat_rx_unicast(stat_rx_unicast),                                            // output wire stat_rx_unicast
  .stat_rx_vlan(stat_rx_vlan),                                                  // output wire stat_rx_vlan
  .stat_rx_pcsl_demuxed(stat_rx_pcsl_demuxed),                                  // output wire [19 : 0] stat_rx_pcsl_demuxed
  .stat_rx_pcsl_number_0(stat_rx_pcsl_number_0),                                // output wire [4 : 0] stat_rx_pcsl_number_0
  .stat_rx_pcsl_number_1(stat_rx_pcsl_number_1),                                // output wire [4 : 0] stat_rx_pcsl_number_1
  .stat_rx_pcsl_number_10(stat_rx_pcsl_number_10),                              // output wire [4 : 0] stat_rx_pcsl_number_10
  .stat_rx_pcsl_number_11(stat_rx_pcsl_number_11),                              // output wire [4 : 0] stat_rx_pcsl_number_11
  .stat_rx_pcsl_number_12(stat_rx_pcsl_number_12),                              // output wire [4 : 0] stat_rx_pcsl_number_12
  .stat_rx_pcsl_number_13(stat_rx_pcsl_number_13),                              // output wire [4 : 0] stat_rx_pcsl_number_13
  .stat_rx_pcsl_number_14(stat_rx_pcsl_number_14),                              // output wire [4 : 0] stat_rx_pcsl_number_14
  .stat_rx_pcsl_number_15(stat_rx_pcsl_number_15),                              // output wire [4 : 0] stat_rx_pcsl_number_15
  .stat_rx_pcsl_number_16(stat_rx_pcsl_number_16),                              // output wire [4 : 0] stat_rx_pcsl_number_16
  .stat_rx_pcsl_number_17(stat_rx_pcsl_number_17),                              // output wire [4 : 0] stat_rx_pcsl_number_17
  .stat_rx_pcsl_number_18(stat_rx_pcsl_number_18),                              // output wire [4 : 0] stat_rx_pcsl_number_18
  .stat_rx_pcsl_number_19(stat_rx_pcsl_number_19),                              // output wire [4 : 0] stat_rx_pcsl_number_19
  .stat_rx_pcsl_number_2(stat_rx_pcsl_number_2),                                // output wire [4 : 0] stat_rx_pcsl_number_2
  .stat_rx_pcsl_number_3(stat_rx_pcsl_number_3),                                // output wire [4 : 0] stat_rx_pcsl_number_3
  .stat_rx_pcsl_number_4(stat_rx_pcsl_number_4),                                // output wire [4 : 0] stat_rx_pcsl_number_4
  .stat_rx_pcsl_number_5(stat_rx_pcsl_number_5),                                // output wire [4 : 0] stat_rx_pcsl_number_5
  .stat_rx_pcsl_number_6(stat_rx_pcsl_number_6),                                // output wire [4 : 0] stat_rx_pcsl_number_6
  .stat_rx_pcsl_number_7(stat_rx_pcsl_number_7),                                // output wire [4 : 0] stat_rx_pcsl_number_7
  .stat_rx_pcsl_number_8(stat_rx_pcsl_number_8),                                // output wire [4 : 0] stat_rx_pcsl_number_8
  .stat_rx_pcsl_number_9(stat_rx_pcsl_number_9),                                // output wire [4 : 0] stat_rx_pcsl_number_9
  .stat_tx_bad_fcs(stat_tx_bad_fcs),                                            // output wire stat_tx_bad_fcs
  .stat_tx_broadcast(stat_tx_broadcast),                                        // output wire stat_tx_broadcast
  .stat_tx_frame_error(stat_tx_frame_error),                                    // output wire stat_tx_frame_error
  .stat_tx_local_fault(stat_tx_local_fault),                                    // output wire stat_tx_local_fault
  .stat_tx_multicast(stat_tx_multicast),                                        // output wire stat_tx_multicast
  .stat_tx_packet_1024_1518_bytes(stat_tx_packet_1024_1518_bytes),              // output wire stat_tx_packet_1024_1518_bytes
  .stat_tx_packet_128_255_bytes(stat_tx_packet_128_255_bytes),                  // output wire stat_tx_packet_128_255_bytes
  .stat_tx_packet_1519_1522_bytes(stat_tx_packet_1519_1522_bytes),              // output wire stat_tx_packet_1519_1522_bytes
  .stat_tx_packet_1523_1548_bytes(stat_tx_packet_1523_1548_bytes),              // output wire stat_tx_packet_1523_1548_bytes
  .stat_tx_packet_1549_2047_bytes(stat_tx_packet_1549_2047_bytes),              // output wire stat_tx_packet_1549_2047_bytes
  .stat_tx_packet_2048_4095_bytes(stat_tx_packet_2048_4095_bytes),              // output wire stat_tx_packet_2048_4095_bytes
  .stat_tx_packet_256_511_bytes(stat_tx_packet_256_511_bytes),                  // output wire stat_tx_packet_256_511_bytes
  .stat_tx_packet_4096_8191_bytes(stat_tx_packet_4096_8191_bytes),              // output wire stat_tx_packet_4096_8191_bytes
  .stat_tx_packet_512_1023_bytes(stat_tx_packet_512_1023_bytes),                // output wire stat_tx_packet_512_1023_bytes
  .stat_tx_packet_64_bytes(stat_tx_packet_64_bytes),                            // output wire stat_tx_packet_64_bytes
  .stat_tx_packet_65_127_bytes(stat_tx_packet_65_127_bytes),                    // output wire stat_tx_packet_65_127_bytes
  .stat_tx_packet_8192_9215_bytes(stat_tx_packet_8192_9215_bytes),              // output wire stat_tx_packet_8192_9215_bytes
  .stat_tx_packet_large(stat_tx_packet_large),                                  // output wire stat_tx_packet_large
  .stat_tx_packet_small(stat_tx_packet_small),                                  // output wire stat_tx_packet_small
  .stat_tx_total_bytes(stat_tx_total_bytes),                                    // output wire [5 : 0] stat_tx_total_bytes
  .stat_tx_total_good_bytes(stat_tx_total_good_bytes),                          // output wire [13 : 0] stat_tx_total_good_bytes
  .stat_tx_total_good_packets(stat_tx_total_good_packets),                      // output wire stat_tx_total_good_packets
  .stat_tx_total_packets(stat_tx_total_packets),                                // output wire stat_tx_total_packets
  .stat_tx_unicast(stat_tx_unicast),                                            // output wire stat_tx_unicast
  .stat_tx_vlan(stat_tx_vlan),                                                  // output wire stat_tx_vlan
  .ctl_tx_enable(ctl_tx_enable),                                                // input wire ctl_tx_enable
  .ctl_tx_send_idle(ctl_tx_send_idle),                                          // input wire ctl_tx_send_idle
  .ctl_tx_send_rfi(ctl_tx_send_rfi),                                            // input wire ctl_tx_send_rfi
  .ctl_tx_send_lfi(ctl_tx_send_lfi),                                            // input wire ctl_tx_send_lfi
  .ctl_tx_test_pattern(ctl_tx_test_pattern),                                    // input wire ctl_tx_test_pattern
  .tx_clk(tx_clk),                                                              // input wire tx_clk
  .stat_tx_pause_valid(stat_tx_pause_valid),                                    // output wire [8 : 0] stat_tx_pause_valid
  .stat_tx_pause(stat_tx_pause),                                                // output wire stat_tx_pause
  .stat_tx_user_pause(stat_tx_user_pause),                                      // output wire stat_tx_user_pause
  .ctl_tx_pause_enable(ctl_tx_pause_enable),                                    // input wire [8 : 0] ctl_tx_pause_enable
  .ctl_tx_pause_quanta0(ctl_tx_pause_quanta0),                                  // input wire [15 : 0] ctl_tx_pause_quanta0
  .ctl_tx_pause_quanta1(ctl_tx_pause_quanta1),                                  // input wire [15 : 0] ctl_tx_pause_quanta1
  .ctl_tx_pause_quanta2(ctl_tx_pause_quanta2),                                  // input wire [15 : 0] ctl_tx_pause_quanta2
  .ctl_tx_pause_quanta3(ctl_tx_pause_quanta3),                                  // input wire [15 : 0] ctl_tx_pause_quanta3
  .ctl_tx_pause_quanta4(ctl_tx_pause_quanta4),                                  // input wire [15 : 0] ctl_tx_pause_quanta4
  .ctl_tx_pause_quanta5(ctl_tx_pause_quanta5),                                  // input wire [15 : 0] ctl_tx_pause_quanta5
  .ctl_tx_pause_quanta6(ctl_tx_pause_quanta6),                                  // input wire [15 : 0] ctl_tx_pause_quanta6
  .ctl_tx_pause_quanta7(ctl_tx_pause_quanta7),                                  // input wire [15 : 0] ctl_tx_pause_quanta7
  .ctl_tx_pause_quanta8(ctl_tx_pause_quanta8),                                  // input wire [15 : 0] ctl_tx_pause_quanta8
  .ctl_tx_pause_refresh_timer0(ctl_tx_pause_refresh_timer0),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer0
  .ctl_tx_pause_refresh_timer1(ctl_tx_pause_refresh_timer1),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer1
  .ctl_tx_pause_refresh_timer2(ctl_tx_pause_refresh_timer2),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer2
  .ctl_tx_pause_refresh_timer3(ctl_tx_pause_refresh_timer3),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer3
  .ctl_tx_pause_refresh_timer4(ctl_tx_pause_refresh_timer4),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer4
  .ctl_tx_pause_refresh_timer5(ctl_tx_pause_refresh_timer5),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer5
  .ctl_tx_pause_refresh_timer6(ctl_tx_pause_refresh_timer6),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer6
  .ctl_tx_pause_refresh_timer7(ctl_tx_pause_refresh_timer7),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer7
  .ctl_tx_pause_refresh_timer8(ctl_tx_pause_refresh_timer8),                    // input wire [15 : 0] ctl_tx_pause_refresh_timer8
  .ctl_tx_pause_req(ctl_tx_pause_req),                                          // input wire [8 : 0] ctl_tx_pause_req
  .ctl_tx_resend_pause(ctl_tx_resend_pause),                                    // input wire ctl_tx_resend_pause
  .tx_ovfout(tx_ovfout),                                                        // output wire tx_ovfout
  .tx_rdyout(tx_rdyout),                                                        // output wire tx_rdyout
  .tx_unfout(tx_unfout),                                                        // output wire tx_unfout
  .tx_datain0(tx_datain0),                                                      // input wire [127 : 0] tx_datain0
  .tx_datain1(tx_datain1),                                                      // input wire [127 : 0] tx_datain1
  .tx_datain2(tx_datain2),                                                      // input wire [127 : 0] tx_datain2
  .tx_datain3(tx_datain3),                                                      // input wire [127 : 0] tx_datain3
  .tx_enain0(tx_enain0),                                                        // input wire tx_enain0
  .tx_enain1(tx_enain1),                                                        // input wire tx_enain1
  .tx_enain2(tx_enain2),                                                        // input wire tx_enain2
  .tx_enain3(tx_enain3),                                                        // input wire tx_enain3
  .tx_eopin0(tx_eopin0),                                                        // input wire tx_eopin0
  .tx_eopin1(tx_eopin1),                                                        // input wire tx_eopin1
  .tx_eopin2(tx_eopin2),                                                        // input wire tx_eopin2
  .tx_eopin3(tx_eopin3),                                                        // input wire tx_eopin3
  .tx_errin0(tx_errin0),                                                        // input wire tx_errin0
  .tx_errin1(tx_errin1),                                                        // input wire tx_errin1
  .tx_errin2(tx_errin2),                                                        // input wire tx_errin2
  .tx_errin3(tx_errin3),                                                        // input wire tx_errin3
  .tx_mtyin0(tx_mtyin0),                                                        // input wire [3 : 0] tx_mtyin0
  .tx_mtyin1(tx_mtyin1),                                                        // input wire [3 : 0] tx_mtyin1
  .tx_mtyin2(tx_mtyin2),                                                        // input wire [3 : 0] tx_mtyin2
  .tx_mtyin3(tx_mtyin3),                                                        // input wire [3 : 0] tx_mtyin3
  .tx_sopin0(tx_sopin0),                                                        // input wire tx_sopin0
  .tx_sopin1(tx_sopin1),                                                        // input wire tx_sopin1
  .tx_sopin2(tx_sopin2),                                                        // input wire tx_sopin2
  .tx_sopin3(tx_sopin3),                                                        // input wire tx_sopin3
  .tx_preamblein(tx_preamblein),                                                // input wire [55 : 0] tx_preamblein
  .tx_reset_done(tx_reset_done),                                                // input wire tx_reset_done
  .rx_reset_done(rx_reset_done),                                                // input wire rx_reset_done
  .rx_serdes_reset_done(rx_serdes_reset_done),                                  // input wire [9 : 0] rx_serdes_reset_done
  .rx_serdes_clk_in(rx_serdes_clk_in),                                          // input wire [9 : 0] rx_serdes_clk_in
  .drp_clk(drp_clk),                                                            // input wire drp_clk
  .drp_addr(drp_addr),                                                          // input wire [9 : 0] drp_addr
  .drp_di(drp_di),                                                              // input wire [15 : 0] drp_di
  .drp_en(drp_en),                                                              // input wire drp_en
  .drp_do(drp_do),                                                              // output wire [15 : 0] drp_do
  .drp_rdy(drp_rdy),                                                            // output wire drp_rdy
  .drp_we(drp_we)                                                              // input wire drp_we
);
// INST_TAG_END ------ End INSTANTIATION Template ---------

// You must compile the wrapper file cmac_usplus_0.v when simulating
// the core, cmac_usplus_0. When compiling the wrapper file, be sure to
// reference the Verilog simulation library.

