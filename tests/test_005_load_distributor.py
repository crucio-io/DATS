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
from dats.remote_control import remote_system


class FiveTupleLookup(dats.test.binsearch.BinarySearch):
    """Load distributor

    This use-case encompasses many of the building blocks of more complex applications:
    load distribution, symmetric load distribution, routing, policing...
    A resource demanding and a general way to formulate these use-cases is in terms of a lookup based on a sufficiently long key extracted from the packet.
    Using this formulation prevents or minimizes exploiting the structure of the underlying data.
    The conventional 5-tuple is used in this test as it requires some extraction steps and allows defining enough distinct values to find the performance limits.
    The load balanced (uniformly) towards any number of output ports.
    The load is increased (adding more ports if needed) while packets are load balanced using a hash table of 8M entries.

    The number of packets per second that can be forwarded determines the KPI. The packet size is 64 bytes.
    In this test packets can be reordered.
    """
    def update_kpi(self, result):
        if result['pkt_size'] != 64:
            return

        self._kpi = '{:.2f} Mpps'.format(result['measurement'])

    def lower_bound(self, pkt_size):
        return 0.0

    def upper_bound(self, pkt_size):
        return 100.0

    def setup_class(self):
        self._tester_cpu_map = self.get_remote('tester').get_cpu_topology()
        self.get_remote('tester').copy_extra_config("parameters.lua")
        self.get_remote('sut').copy_extra_config("parameters.lua")
        self._tester = self.get_remote('tester').run_prox_with_config("gen_5tuplookup-4.cfg", "-e -t", "Tester")

        self._sut = self.get_remote('sut')
        self._sut.copy_extra_config("tuples.lua")

        self._sut.run_prox_with_config("handle_5tuplookup-4.cfg", "-t", "SUT")

    def teardown_class(self):
        pass

    def run_test(self, pkt_size, duration, value):
        cores = [
            self.get_cpu_id(self._tester_cpu_map, 1, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 2, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 3, int(config.getOption("testerSocketId")), False),
            self.get_cpu_id(self._tester_cpu_map, 4, int(config.getOption("testerSocketId")), False),
        ]

        self._tester.stop_all()
        self._tester.reset_stats()
        self._tester.set_pkt_size(cores, pkt_size)
        self._tester.set_speed(cores, value)
        self._tester.start_all()

        # Getting statistics to calculate PPS at right speed....
        tsc_hz = self._tester.hz()
        sleep(2)
        rx_start, tx_start, tsc_start = self._tester.tot_stats()
        sleep(duration)
        # Get stats before stopping the cores. Stopping cores takes some time
        # and might skew results otherwise.
        rx_stop, tx_stop, tsc_stop = self._tester.tot_stats()
        self._tester.stop_all()

        port_stats = self._tester.port_stats([0, 1, 2, 3])
        rx_total = port_stats[6]
        tx_total = port_stats[7]

        can_be_lost = int(tx_total * float(config.getOption('toleratedLoss')) / 100.0)
        logging.verbose("RX: %d; TX: %d; dropped: %d (tolerated: %d)", rx_total, tx_total, tx_total - rx_total, can_be_lost)

        # calculate the effective throughput in Mpps
        tx = tx_stop - tx_start
        tsc = tsc_stop - tsc_start
        mpps = tx / (tsc/float(tsc_hz)) / 1000000

        pps = (value / 100.0) * utils.line_rate_to_pps(pkt_size, 4)
        logging.verbose("Mpps configured: %f; Mpps effective %f", (pps/1000000.0), mpps)

        return (tx_total - rx_total <= can_be_lost), mpps, 100.0*(tx_total - rx_total)/float(tx_total)
