#
# Dataplane Automated Testing System
#
# Copyright (c) 2016, Viosoft Corporation.
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

import dats.test.latencybase


class LatencyTest(dats.test.latencybase.LatencyBase):
    """Latency Test

    This test measures the latency on (n) cores running latency task 'lat'
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
        self._tester = self.get_remote('tester').run_prox_with_config("lat-gen.cfg", "-e -t", "Tester")

    def teardown_class(self):
        pass

    def run_test(self, pkt_size, duration):
        core_tx = 1
        lat_core = 2  # Core Running 'lat' Task

        self._tester.stop_all()
        self._tester.reset_stats()
        self._tester.set_pkt_size([core_tx], pkt_size)
        self._tester.set_speed([core_tx], self.upper_bound(pkt_size))
        self._tester.start_all()

        core_id = (lat_core * 2) + 1
        lat_min, lat_max, lat_avg = self._tester.lat_stats([core_id])

        self._tester.stop_all()

        return lat_min[core_id], lat_max[core_id], lat_avg[core_id]
