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

            # time duration of a single step
            duration = float(config.getOption('testDuration'))
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
        precision = float(config.getOption('testPrecision'))

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

        # throughput and packet loss from the last successfull test
        successfull_throughput = 0
        successfull_pkt_loss = 0
        while upper - lower >= precision:
            logging.verbose("New interval [%s, %s), precision: %d",
                lower, upper, upper - lower)
            logging.info("Testing with value %s", test_value)

            self.setup_test(pkt_size=pkt_size, speed=test_value)
            success, throughput, pkt_loss = self.run_test(pkt_size, duration, test_value)
            self.teardown_test(pkt_size=pkt_size)

            if success:
                logging.verbose("Success! Increasing lower bound")
                lower = test_value
                successfull_throughput = throughput
                successfull_pkt_loss = pkt_loss
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
            pkt_loss=successfull_pkt_loss
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

    def get_cpu_id(self, cpu_map, core_id, socket_id, is_hyperthread):
        try:
            return cpu_map[socket_id][core_id][1 if is_hyperthread else 0]
        except:
            raise Exception("Core {}{} on socket {} does not exist" \
                    .format(str(core_id), "h" if is_hyperthread else "", str(socket_id)))


    def generate_report(self, results, prefix, dir):
        # Generate graph of results
        table = [[ 'Packet size (B)', 'Throughput (Mpps)', 'Theoretical Max (Mpps)']]
        for result in results:
            # TODO move formatting to <typeof(measurement)>.__str__
            table.append([
                result['pkt_size'],
                result['measurement'],
                round(utils.line_rate_to_pps(result['pkt_size'], float(self._n_ports)) / 1000000, 2),
            ])
        dats.plot.bar_plot(table, dir + prefix + 'results.png')

        # Generate table
        table = [['Packet size (B)', 'Throughput (Mpps)', 'Theoretical Max (Mpps)', 'Duration (s)', 'Packet loss (%)']]
        for result in results:
            # TODO move formatting to <typeof(measurement)>.__str__
            table.append([
                result['pkt_size'],
                "{:.2f}".format(result['measurement']),
                "{:.2f}".format(round(utils.line_rate_to_pps(result['pkt_size'], float(self._n_ports)) / 1000000, 2)),
                "{:.1f}".format(round(result['duration'], 1)),
                "{:.5f}".format(round(result['pkt_loss'], 5)),
            ])

        # Generate reStructuredText report
        report = ''
        report += '.. image:: ' + prefix + 'results.png\n'
        report += '\n'
        report += rst.simple_table(table)

        return report
    def generate_json(self, results):
        test_results = dict()
        index = 0
        for result in results:
            result_dict = dict()
            result_dict['PacketSize(B)'] = "{}".format(result['pkt_size'])
            result_dict['Throughput(Mpps)'] = "{:.2f}".format(result['measurement'])
            result_dict['TheoreticalMax(Mpps)'] = "{:.2f}".format(round(utils.line_rate_to_pps(result['pkt_size'], float(self._n_ports)) / 1000000, 2))
            result_dict['Duration(s)'] = "{:.1f}".format(round(result['duration'], 1))
            result_dict['PacketLoss(%)'] = round(result['pkt_loss'], 5)
            test_results["pkt_test_" + str(index)] = result_dict
            index += 1
        return test_results

    def generate_csv(self, results):
        csv_string = 'Packet size (B),Throughput (Mpps),Theoretical Max (Mpps),Duration (s),Packet loss (%)\n'
        
        # add data lines
        for result in results:
            csv_string += "{},{:.2f},{:.2f},{:.1f},{:.5f}\n".format(result['pkt_size'],
                result['measurement'],
                round(utils.line_rate_to_pps(result['pkt_size'], 4) / 1000000, 2),
                round(result['duration'], 1),
                round(result['pkt_loss'], 5))

        return csv_string

