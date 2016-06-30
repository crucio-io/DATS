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

"""
The interface for the tests that perform a binary search.

This abstract base class defines the common properties and methods for tests
that perform a binary search.

The binary search algorithm is also implemented here.
"""
from __future__ import division

import abc
import time
import logging

import dats.test.base
import dats.config as config
import dats.plot
import dats.utils as utils
import dats.rstgen as rst


class RampBase(dats.test.base.TestBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Initialize the test object.
        """
        super(RampBase, self).__init__()

    @abc.abstractproperty
    def start_interval(self):
        """Return the start interval of the linear search.
        """
        return

    @abc.abstractproperty
    def step_interval(self):
        """Return the step size of a linear search.
        """
        return

    def min_pkt_size(self):
        """Return the minimum required packet size for the test.

        Defaults to 64. Individual test must override this method if they have
        other requirements.

        Returns:
            int. The minimum required packet size for the test.
        """
        return 64

    @abc.abstractproperty
    def latency_cores(self):
        """Returns the cores running on latency modeself.

        Args:
            None

        Returns:
            Array of all cores running on mode latency
        """
        return

    def run_all_tests(self):
        """Iterate over requested packet sizes and search for the maximum value that yields success.

        Returns:
            [{...}]. An array with a dict per packet size the test has run
            with.
            See run_test_with_pkt_size() for a description of the dicts. The
            following keys are added to the dicts:
            pkt_size (int): The packet size used when measuring
            duration (float): The duration of the search in seconds
        """
        results = []

        pkt_sizes = map(int, config.getOption('pktSizes').split(','))
        for pkt_size in pkt_sizes:
            # Adjust packet size upwards if it's less than the minimum
            # required packet size for the test.
            if pkt_size < self.min_pkt_size():
                pkt_size += self.min_pkt_size() - 64

            logging.info("Testing with packet size %d", pkt_size)
            test_value = self.start_interval()

            while test_value <= 100:
                # FIXME get duration from config file
                duration = 5
                start_time = time.time()
                result = self.run_test_with_pkt_size(pkt_size, duration, test_value)
                stop_time = time.time()
                result['pkt_size'] = pkt_size
                result['duration'] = stop_time - start_time
                result['test_value'] = test_value
                results.append(result)
                test_value = test_value + self.step_interval()

        return results

    def run_test_with_pkt_size(self, pkt_size, duration, test_value):
        """Run the test for a single packet size.

        Args:
            pkt_size (int): The packet size to test with.
            duration (int): The duration for each try.

        Returns:
            {lower_bound, upper_bound, measurement}.
            lower_bound (long): The lower bound of the search interval.
            upper_bound (long): The upper bound of the search interval.
            measurement (long): The maximum value in the interval that yields
            latency (dict): latency results
            success.
        """

        logging.info("Testing with value %s", test_value)

        self.setup_test(pkt_size=pkt_size, speed=test_value)
        success, throughput, pkt_loss, lat = self.run_test(pkt_size, duration, test_value)
        self.teardown_test(pkt_size=pkt_size)

        if success:
            logging.verbose("Success! Increasing lower bound")
        else:
            logging.verbose("Failure... Decreasing upper bound")

        return dict(
            measurement=throughput,
            pkt_loss=pkt_loss,
            latency=lat
        )

    @abc.abstractmethod
    def run_test(self, pkt_size, duration, value):
        """Execute a test run with the specified duration and packet size.

        Args:
            pkt_size (int): The packet size to use for this test run
            duration (int): The duration in seconds for the test
            value (long): The value to test with.

        Returns:
            bool. True if test succeeds, False if test fails.
            int throughput in Mpps
            int total packet loss
        """
        return

    def generate_report(self, results, prefix, dir):
        # latency cores
        cores = self.latency_cores()

        pkt_size = 0
        report = ''

        # Create a list of pkt_sizes contained in results[]
        pkt_sizes = []
        for result in results:
            if result['pkt_size'] not in pkt_sizes:
                pkt_sizes.append(result['pkt_size'])

        for pkt_size in pkt_sizes:

            # Table for each pkt_size
            table = [[
                'Packet size (B)', 'Test Value (%)', 'Throughput (Mpps)', 'Theoretical Max (Mpps)',
                'Average Latency (ns)', 'Duration (s)', 'Packet loss (%)'
            ]]

            plot_table = [['', '', '']]

            for result in results:
                if (result['pkt_size'] != pkt_size):
                    continue
                latency = result['latency']
                lat_avg = latency['latency_avg']
                total_avg_lat = 0
                for core in cores:
                    total_avg_lat = total_avg_lat + lat_avg[core]
                total_avg_lat = total_avg_lat / len(cores)

                table.append([
                    result['pkt_size'],
                    result['test_value'],
                    "{:.2f}".format(result['measurement']),
                    "{:.2f}".format(round(utils.line_rate_to_pps(result['pkt_size'], 4) / 1000000, 2)),
                    "{:.2f}".format(total_avg_lat),
                    "{:.1f}".format(round(result['duration'], 1)),
                    "{:.5f}".format(round(result['pkt_loss'], 5))])

                plot_table.append([
                    result['test_value'],
                    "{:.2f}".format(result['measurement']),
                    total_avg_lat])

            # Generate reStructuredText report
            dats.plot.plot_throughput_latency(plot_table, dir + prefix + 'ramp_results_{}.png'.format(pkt_size))

            report += rst.section('Packet Size {}'.format(pkt_size), '-')
            report += '.. image:: ' + prefix + 'ramp_results_{}.png\n'.format(pkt_size)
            report += '\n'
            report += rst.simple_table(table)
            report += '\n\n'

        return report
