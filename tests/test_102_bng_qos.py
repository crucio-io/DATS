#
# Dataplane Automated Testing System
#
# Copyright (c) 2015-2016, Intel Corporation.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from time import sleep
import logging

import dats.test.binsearch
import dats.utils as utils
import dats.config as config

class BNG_QoS(dats.test.binsearch.BinarySearch):
    """BNG with QoS

    The BNG+QoS workload converts packets from QinQ to GRE tunnels, handles
    routing, adds/removes MPLS tags and performs QoS.

    This use case simulates a realistic and complex application. The number of
    users is 32K per port and the number of routes is 8K.

    Four ports are required to run the default configuration of this workload.
    """

    def update_kpi(self, result):
        if result['pkt_size'] != 78:
            return

        self._kpi = '{} Mpps'.format(result['measurement'])

    def lower_bound(self, pkt_size):
        return 0.0

    def upper_bound(self, pkt_size):
        return 100.0

    def min_pkt_size(self):
        return 78

    def setup_class(self):
        self._tester_cpu_map = self.get_remote('tester').get_cpu_topology()
        self.get_remote('tester').copy_extra_config("parameters.lua")
        self.get_remote('sut').copy_extra_config("parameters.lua")
        self._tester = self.get_remote('tester').run_prox_with_config("gen_bng_qos-4.cfg", "-e -t", "Tester")

        sut = self.get_remote('sut')
        sut.copy_extra_config("gre_table.lua")
        sut.copy_extra_config("ipv4.lua")
        sut.copy_extra_config("dscp.lua")

        self._sut = sut.run_prox_with_config("handle_bng_qos-4.cfg", "-t", "SUT")

        # These should go to the configuration file and eventually should be
        # autoprobed.
        self._cpe_cores = [
            self.get_cpu_id(self._tester_cpu_map, 2, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 4, int(config.getOption("testerSocketId")), False),
        ]
        self._inet_cores = [
            self.get_cpu_id(self._tester_cpu_map, 5, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 6, int(config.getOption("testerSocketId")), False),
        ]
        self._arp_cores = [
            self.get_cpu_id(self._tester_cpu_map, 1, int(config.getOption("testerSocketId")), False),
        ]
        self._all_rx_cores = [
            self.get_cpu_id(self._tester_cpu_map, 3, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 7, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 8, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 9, int(config.getOption("testerSocketId")), False),
        ]
        self._rx_lat_cores = [
            self.get_cpu_id(self._tester_cpu_map, 3, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 7, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 8, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 9, int(config.getOption("testerSocketId")), False),
        ]
        self._all_stats_cores = self._cpe_cores + self._inet_cores + self._all_rx_cores

        self._step_delta = 1
        self._step_time = 0.5

    def teardown_class(self):
        pass


    # Initialization before the test proper consists of two parts:
    # - ARP: The tables of the SUT are initialized by ARP packets. 4 seconds
    #       will be sent before the test starts, so the tables are already
    #       filled when testing begins.
    # - Ramp up sending speeds: performance is better when the sending speed
    #       is increased in a few steps, instead of sending packets at full
    #       speed immediately.
    def setup_test(self, pkt_size, speed):
        # Calculate the target upload and download speed. The upload and
        # download packets have different packet sizes, so in order to get
        # equal bandwidth usage, the ratio of the speeds has to match the ratio
        # of the packet sizes.
        inet_pkt_size = pkt_size
        cpe_pkt_size  = pkt_size - 24
        ratio = 1.0 * (cpe_pkt_size + 20) / (inet_pkt_size + 20)

        curr_up_speed = curr_down_speed = 0
        max_up_speed = max_down_speed = speed
        if ratio < 1:
            max_down_speed = speed * ratio
        else:
            max_up_speed = speed / ratio

        # Initialize cores
        logging.verbose("Initializing tester")
        self._tester.stop_all()
        sleep(0.5)
        # Flush any packets in the NIC RX buffers, otherwise the stats will be
        # wrong.
        self._tester.start(self._all_rx_cores)
        sleep(0.5)
        self._tester.stop(self._all_rx_cores)
        sleep(0.5)
        self._tester.reset_stats()

        self._tester.set_pkt_size(self._inet_cores, inet_pkt_size)
        self._tester.set_pkt_size(self._cpe_cores, cpe_pkt_size)

        self._tester.reset_values(self._cpe_cores)
        self._tester.reset_values(self._inet_cores)

        # Set correct IP and UDP lengths in packet headers
        ## CPE
        # IP length (byte 24): 26 for MAC(12), EthType(2), QinQ(8), CRC(4)
        self._tester.set_value(self._cpe_cores, 24, cpe_pkt_size - 26, 2)
        # UDP length (byte 46): 46 for MAC(12), EthType(2), QinQ(8), IP(20), CRC(4)
        self._tester.set_value(self._cpe_cores, 46, cpe_pkt_size - 46, 2)

        ## INET
        # IP length (byte 20): 22 for MAC(12), EthType(2), MPLS(4), CRC(4)
        self._tester.set_value(self._inet_cores, 20, inet_pkt_size - 22, 2)
        # IP length (byte 48): 50 for MAC(12), EthType(2), MPLS(4), IP(20), GRE(8), CRC(4)
        self._tester.set_value(self._inet_cores, 48, inet_pkt_size - 50, 2)
        # UDP length (byte 70): 70 for MAC(12), EthType(2), MPLS(4), IP(20), GRE(8), IP(20), CRC(4)
        self._tester.set_value(self._inet_cores, 70, inet_pkt_size - 70, 2)

        # Sending ARP to initialize tables - need a few seconds of generation
        # to make sure all CPEs are initialized
        logging.verbose("Initializing SUT: sending ARP packets")
        self._tester.set_speed(self._arp_cores, 1)
        self._tester.set_speed(self._inet_cores, curr_up_speed)
        self._tester.set_speed(self._cpe_cores, curr_down_speed)
        self._tester.start(self._arp_cores)
        sleep(4)

        # Ramp up the transmission speed. First go to the common speed, then
        # increase steps for the faster one.
        self._tester.start(self._cpe_cores + self._inet_cores + self._rx_lat_cores)

        logging.verbose("Ramping up speed to %s up, %s down", str(max_up_speed), str(max_down_speed))
        while (curr_up_speed < max_up_speed) or (curr_down_speed < max_down_speed):
            # The min(..., ...) takes care of 1) floating point rounding errors
            # that could make curr_*_speed to be slightly greater than
            # max_*_speed and 2) max_*_speed not being an exact multiple of
            # self._step_delta.
            if curr_up_speed < max_up_speed:
                curr_up_speed = min(curr_up_speed + self._step_delta, max_up_speed)
            if curr_down_speed < max_down_speed:
                curr_down_speed = min(curr_down_speed + self._step_delta, max_down_speed)

            self._tester.set_speed(self._inet_cores, curr_up_speed)
            self._tester.set_speed(self._cpe_cores, curr_down_speed)
            sleep(self._step_time)
        logging.verbose("Target speeds reached. Starting real test.")

    def run_test(self, pkt_size, duration, value):
        # Tester is sending packets at the required speed already after
        # setup_test(). Just get the current statistics, sleep the required
        # amount of time and calculate packet loss.

        # Getting statistics to calculate PPS at right speed....
        tsc_hz = self._tester.hz()
        rx_start, tx_start, tsc_start = self._tester.tot_stats()
        sleep(duration)
        # Get stats before stopping the cores. Stopping cores takes some time
        # and might skew results otherwise.
        rx_stop, tx_stop, tsc_stop = self._tester.tot_stats()
        # TODO report latency?
        lat_min, lat_max, lat_avg = self._tester.lat_stats(self._rx_lat_cores)

        self._tester.stop(self._arp_cores + self._cpe_cores + self._inet_cores)
        # flush packets in NIC RX buffers so they are counted too when
        # when calculating the number of dropped packets.
        logging.verbose("Test ended. Flushing NIC buffers")
        self._tester.start(self._all_rx_cores)
        sleep(3)
        self._tester.stop(self._all_rx_cores)

        # calculate the effective throughput in Mpps
        rx = rx_stop - rx_start
        tsc = tsc_stop - tsc_start
        mpps = rx / (tsc/float(tsc_hz)) / 1000000
        logging.verbose("MPPS: %f", mpps)

        rx_tot, tx_tot, drop_tot, _ = self._tester.rx_stats(self._all_stats_cores)

        can_be_lost = int(tx_tot * float(config.getOption('toleratedLoss')) / 100.0)
        logging.verbose("RX: %d; TX: %d; drop: %d; TX-RX: %d (tolerated: %d)", rx_tot, tx_tot, drop_tot, tx_tot - rx_tot, can_be_lost)

        return (tx_tot - rx_tot <= can_be_lost), mpps, 100.0*(tx_tot - rx_tot)/float(tx_tot)
