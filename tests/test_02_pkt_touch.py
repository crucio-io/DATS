# Dataplane Automated Testing System
# Copyright (c) 2015, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
#

from time import sleep
import logging

import dats.test.binsearch
import dats.utils as utils
import dats.config as config
from dats.remote_control import remote_system


class ForwardPacketsTouch(dats.test.binsearch.BinarySearch):
    """Port forwarding with touching packets

    The application will take packets in from one port, update src and dst MACs
    and forward them to another port.

    The KPI is the number of packets per second for 64 byte packets with an
    accepted minimal packet loss.
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
        self._tester = self.get_remote('tester').run_prox_with_config("gen_all-4.cfg", "-e -t", "Tester")
        self._sut = self.get_remote('sut').run_prox_with_config("handle_touch-4.cfg", "-t", "SUT")

    def teardown_class(self):
        pass

    def run_test(self, pkt_size, duration, value):
        cores = [1, 2, 3, 4]

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

        return (tx_total - rx_total <= can_be_lost), mpps
