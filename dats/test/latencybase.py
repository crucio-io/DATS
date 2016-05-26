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
The interface for the tests that perform an iteration on packet sizes in order
to perform latency test.

This abstract base class defines the common properties and methods for tests
that run of different packet sizes.

"""

import abc
import time
import logging

import dats.test.base
import dats.config as config
import dats.plot
import dats.rstgen as rst


class LatencyBase(dats.test.base.TestBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Initialize the test object.
        """
        super(LatencyBase, self).__init__()

    @abc.abstractproperty
    def lower_bound(self, pkt_size):
        """Return the lower bound of the interval for the latency test.

        Args:
            pkt_size (int): The packet size to get the lower bound for.

        Returns:
            long. The lower bound of the interval to test.
        """
        return

    @abc.abstractproperty
    def upper_bound(self, pkt_size):
        """Return the upper bound of the interval for the latency test.

        Args:
            pkt_size (int): The packet size to get the upper bound for.

        Returns:
            long. The upper bound of the interval to test.
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

    def run_all_tests(self):
        """Iterate over requested packet sizes.

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

            # FIXME get duration from config file
            duration = 5
            start_time = time.time()
            result = self.run_test_with_pkt_size(pkt_size, duration)
            stop_time = time.time()
            result['pkt_size'] = pkt_size
            result['duration'] = stop_time - start_time

            results.append(result)

        return results

    def run_test_with_pkt_size(self, pkt_size, duration):
        """Run the test for a single packet size.

        Args:
            pkt_size (int): The packet size to test with.
            duration (int): The duration for each try.

        Returns:
            {lower_bound, upper_bound, measurement}.
            lower_bound (long): The lower bound of the search interval.
            upper_bound (long): The upper bound of the search interval.
            measurement (long): The maximum value in the interval that yields
            success.
        """

        logging.info("Testing with packet size %d", pkt_size)
        self.setup_test(pkt_size=pkt_size)

        lat_min, lat_max, lat_avg = self.run_test(pkt_size, duration)

        self.teardown_test(pkt_size=pkt_size)

        return dict(
            lower_bound=self.lower_bound(pkt_size),
            upper_bound=self.upper_bound(pkt_size),
            minimum_latency=lat_min,
            maximum_latency=lat_max,
            average_latency=lat_avg,
        )

    @abc.abstractmethod
    def run_test(self, pkt_size, duration):
        """Execute a test run with the specified duration and packet size.

        Args:
            pkt_size (int): The packet size to use for this test run
            duration (int): The duration in seconds for the test

        Returns:
            Minimum Latency, Maximum Latency, Average Latency
        """
        return

    def generate_report(self, results, prefix, dir):
        # Generate graph of results
        table = [['Packet size (B)', 'Maximum Latency (ns)', 'Average Latency (ns)']]
        for result in results:
            # TODO move formatting to <typeof(measurement)>.__str__
            table.append([result['pkt_size'], result['maximum_latency'], result['average_latency']])

        dats.plot.bar_plot(table, dir + prefix + 'results.png')

        # Generate table
        table = [['Packet size (B)', 'Minimum Latency (ns)', 'Maximum Latency (ns)', 'Average Latency (ns)', 'Duration (s)']]
        for result in results:
            # TODO move formatting to <typeof(measurement)>.__str__
            table.append([
                result['pkt_size'],
                "{:.2f}".format(result['minimum_latency']),
                "{:.2f}".format(result['maximum_latency']),
                "{:.2f}".format(result['average_latency']),
                "{:.1f}".format(round(result['duration'], 1))])

        # Generate reStructuredText report
        report = ''
        report += '.. image:: ' + prefix + 'results.png\n'
        report += '\n'
        report += rst.simple_table(table)

        return report
