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

"""
The interface for the tests that perform a binary search.

This abstract base class defines the common properties and methods for tests
that perform a binary search.

The binary search algorithm is also implemented here.
"""

import abc
import time
import logging

import dats.test.base
import dats.config as config
import dats.plot
import dats.utils as utils
import dats.rstgen as rst


class BinarySearch(dats.test.base.TestBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """Initialize the test object.
        """
        super(BinarySearch, self).__init__()

    @abc.abstractproperty
    def lower_bound(self, pkt_size):
        """Return the lower bound of the interval for the binary search.

        Args:
            pkt_size (int): The packet size to get the lower bound for.

        Returns:
            long. The lower bound of the interval to search in.
        """
        return

    @abc.abstractproperty
    def upper_bound(self, pkt_size):
        """Return the upper bound of the interval for the binary search.

        Args:
            pkt_size (int): The packet size to get the upper bound for.

        Returns:
            long. The upper bound of the interval to search in.
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

            ### FIXME get duration from config file
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
        precision = 1   # FIXME get from config file

        lower = self.lower_bound(pkt_size)
        upper = self.upper_bound(pkt_size)

        logging.info("Testing with packet size %d", pkt_size)

        # Binary search assumes the lower value of the interval is
        # successful and the upper value is a failure.
        # The first value that is tested, is the maximum value. If that
        # succeeds, no more searching is needed. If it fails, a regular
        # binary search is performed.
        # The test_value used for the first iteration of binary search
        # is adjusted so that the delta between this test_value and the
        # upper bound is a power-of-2 multiple of precision. In the
        # optimistic situation where this first test_value results in a
        # success, the binary search will complete on an integer multiple
        # of the precision, rather than on a fraction of it.
        adjust = precision
        while upper - lower > adjust:
            adjust *= 2
        adjust = (upper - lower - adjust) / 2

        test_value = upper
        successfull_throughput = 0
        while upper - lower >= precision:
            logging.verbose("New interval [%s, %s), precision: %d",
                lower, upper, upper - lower)
            logging.info("Testing with value %s", test_value)

            self.setup_test(pkt_size=pkt_size, speed=test_value)
            success, throughput = self.run_test(pkt_size, duration, test_value)
            self.teardown_test(pkt_size=pkt_size)

            if success:
                logging.verbose("Success! Increasing lower bound")
                lower = test_value
                successfull_throughput = throughput
            else:
                logging.verbose("Failure... Decreasing upper bound")
                upper = test_value

            test_value = lower + (upper - lower) / 2 + adjust
            adjust = 0

        successfull_throughput = round(successfull_throughput, 2)
        self.update_kpi(dict(pkt_size=pkt_size, measurement=successfull_throughput))

        return dict(
            lower_bound=self.lower_bound(pkt_size),
            upper_bound=self.upper_bound(pkt_size),
            measurement=successfull_throughput,
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
        """
        return


    def generate_report(self, results, prefix, dir):
        # Generate graph of results
        table = [[ 'Packet size (B)', 'Throughput (Mpps)', 'Theoretical Max (Mpps)' ]]
        for result in results:
            # TODO move formatting to <typeof(measurement)>.__str__
            table.append([
                result['pkt_size'],
                result['measurement'],
                round(utils.line_rate_to_pps(result['pkt_size'], 4) / 1000000, 2),
            ])
        dats.plot.bar_plot(table, dir + prefix + 'results.png')

        # Generate table
        table = [['Packet size (B)', 'Throughput (Mpps)', 'Theoretical Max (Mpps)', 'Duration (s)']]
        for result in results:
            # TODO move formatting to <typeof(measurement)>.__str__
            table.append([
                result['pkt_size'],
                "{:.2f}".format(result['measurement']),
                "{:.2f}".format(round(utils.line_rate_to_pps(result['pkt_size'], 4) / 1000000, 2)),
                "{:.1f}".format(round(result['duration'], 1)) ])

        # Generate reStructuredText report
        report = ''
        report += '.. image:: ' + prefix + 'results.png\n'
        report += '\n'
        report += rst.simple_table(table)

        return report

