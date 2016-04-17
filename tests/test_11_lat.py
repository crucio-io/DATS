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
