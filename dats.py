#!/usr/bin/env python2.7

#
# Dataplane Automated Testing System
#
# Copyright (c) 2015-2016, Intel Corporation.
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

import inspect
import argparse
import logging
import sys
import traceback
import os
from datetime import datetime
import re
import imp
import json

import dats.config as config
from dats.doc import res_table
import dats.remote_control as rc
import dats.test
from dats.test.base import TestBase
import dats.rstgen as rst



### DATS version
__version__ = "0.33"


def parse_cmdline():
    """Parse the command line arguments.

    Returns:
        argparse.Namespace. The parsed arguments or defaults.
    """
    parser = argparse.ArgumentParser(
        description="Dataplane Automated Testing System, version " + __version__,
        epilog='Note: parameters on the command line will override values set in the configuration file.')

    parser.add_argument('-d', '--tests-directory',
        default='./tests', metavar='DIRECTORY', dest='tests_dir',
        help='Directory containing test scripts, ./tests/ by default')
    parser.add_argument('-f', '--config',
        default='./dats.cfg',
        help='Configuration file name, ./dats.cfg by default')
    parser.add_argument('-l', '--list',
        action='store_true',
        help='List valid names of test cases and exit')
    parser.add_argument('-r', '--report',
        default=datetime.now().strftime('dats-report-%Y%m%d_%H%M%S/'),
        metavar='DIRECTORY', dest='report_dir',
        help='Where to save the report. A new directory with timestamp in its name is created by default.')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Verbose output - set log level of screen to VERBOSE instead of INFO')
    parser.add_argument(
        'test', nargs='*',
        help='List of test names to execute. All tests are executed by default.')

    args = parser.parse_args()
    return args


def read_configfile(args):
    ### Read config file
    try:
        config.parseFile(args.config)
    except IOError:
        print "Could not read config file " + args.config
        sys.exit(1)


def setup_logging():
    # Add VERBOSE loglevel between DEBUG and INFO and
    logging.addLevelName(15, 'VERBOSE')

    # Add convenience function logging.verbose(...)
    logging.VERBOSE = 15
    def verbose(msg, *args, **kwargs):
        logging.log(logging.VERBOSE, msg, *args, **kwargs)
    logging.verbose = verbose


    # Add TRACE loglevel between NOTSET and DEBUG
    logging.addLevelName(5, 'TRACE')

    # Add convenience function logging.trace(...)
    logging.TRACE = 5
    def trace(msg, *args, **kwargs):
        logging.log(logging.TRACE, msg, *args, **kwargs)
    logging.trace = trace


    # Log to file and to screen
    logging.basicConfig(filename=config.getOption('logFile'),
            format=config.getOption('logFormat'),
            datefmt=config.getOption('logDateFormat'),
            level=config.getOption('logLevel'),
            filemode='w' if config.getOption('logOverwrite') else 'a',
    )

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter(fmt='%(asctime)-8s %(levelname)-8s %(message)s',
            datefmt='%H:%M:%S')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.info("Running DATS version %s", __version__)

    if config.getArg('verbose'):
        console.setLevel(logging.VERBOSE)

def execute_inf_commands(sut_inf_commands, sut_information):
    sut = rc.remote_system(config.getOption('sutUser'), config.getOption('sutIp'),
            config.getOption('sutDpdkDir'), config.getOption('sutDpdkTgt'),
            config.getOption('sutProxDir'))

    for cmd in sut_inf_commands:
        output = sut.run_cmd(cmd[0])['out']
        label = cmd[1] if len(cmd) > 1 else cmd[0]
        output_list = output.split('\n')

        if len(output_list) == 1:
            sut_information.append([label, re.escape(output).replace('\ ', ' ')])
        else:
            # if the output contains more than 1 line
            # count each unique line and print it on a separate row
            current_line = output_list[0]
            nlines = 1
            for line in output_list[1:]:
                if line == current_line:
                    nlines += 1
                else:
                    sut_information.append([label, str(nlines) + "x " + re.escape(line).replace('\ ', ' ')])
                    current_line = line
            sut_information.append([label, str(nlines) + "x " + re.escape(line).replace('\ ', ' ')])

def main():
    print "Dataplane Automated Testing System, version " + __version__
    print "Copyright (c) 2015-2016, Intel Corporation. All rights reserved."
    print "Copyright (c) 2016, Viosoft Corporation. All rights reserved."
    print

    args = parse_cmdline()
    config.set_cmdline_args(args)

    read_configfile(args)
    setup_logging()

    logging.debug("Command line arguments: %s", args)

    all_tests = dats.test.get_tests(args.tests_dir)

    if args.list:
        print "Tests in directory " + args.tests_dir + ": " + ' '.join(sorted(all_tests.keys()))
        sys.exit(0)


    # SUT information
    sut_information_hw = [["Hardware"]]
    sut_inf_commands_hw = [
            ["sudo dmidecode --type system | grep 'Product Name' | cut -d: -f2 2> /dev/null", "Platform"],
            ["grep 'model name' /proc/cpuinfo | uniq | cut -d : -f 2 | cut -c 2- 2> /dev/null", "Processor"],
            ["cat /proc/cpuinfo | grep processor | wc -l", "# of cores"],
            ["printf '%d MB' \\$(free -m | grep Mem | tr -s ' ' | cut -d' ' -f2)", "RAM"],
            [config.getOption("sutDpdkDir") + "/tools/dpdk_nic_bind.py --status | grep  drv=igb_uio | cut -d\\' -f 2", "DPDK ports"],
    ]
    sut_information_sw = [["Software"]]
    sut_inf_commands_sw = [
            ["sudo dmidecode --type bios | grep 'Version' | cut -d: -f2 2> /dev/null", "BIOS version"],
            ["sudo dmidecode --type bios | grep 'Release Date' | cut -d: -f2 2> /dev/null", "BIOS release date"],
            ["sed '1!d' /etc/*-release", "OS"],
            ["uname -rm", "Kernel"],
            ["printf 'v%d.%d' "
                + "\\$(grep '#define VERSION_MAJOR' "
                + config.getOption('sutProxDir') + "/version.h "
                + "| sed 's/[^0-9]//g') "
                + "\\$(grep '#define VERSION_MINOR' "
                + config.getOption('sutProxDir') + "/version.h "
                + "| sed 's/[^0-9]//g')",
              "PROX version"],
            ["printf 'v%d.%d.%d' "
                + "\\$(grep '#define RTE_VER_MAJOR' "
                + config.getOption('sutDpdkDir') + "/lib/librte_eal/common/include/rte_version.h "
                + "| sed 's/[^0-9]//g') "
                + "\\$(grep '#define RTE_VER_MINOR' "
                + config.getOption('sutDpdkDir') + "/lib/librte_eal/common/include/rte_version.h "
                + "| sed 's/[^0-9]//g') "
                + "\\$(grep '#define RTE_VER_PATCH_LEVEL' "
                + config.getOption('sutDpdkDir') + "/lib/librte_eal/common/include/rte_version.h "
                + "| sed 's/[^0-9]//g') ",
              "DPDK version"],
            ["cat /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages 2>/dev/null",
                "Hugepages - 2048kB"],
            ["cat /sys/devices/system/node/node0/hugepages/hugepages-1048576kB/nr_hugepages 2>/dev/null",
                "Hugepages - 1GB"],
            #["uname -a"],
            #["cat /proc/cmdline"],
            #["lspci | grep 82599 | cut -d ' ' -f1", "Niantic ports"],
            #["lspci | grep X710 | cut -d ' ' -f1", "Fortville ports"],
    ]

    logging.info("Retrieving SUT hardware description")
    execute_inf_commands(sut_inf_commands_hw, sut_information_hw)
    logging.info("Retrieving SUT software description")
    execute_inf_commands(sut_inf_commands_sw, sut_information_sw)


    ### Main program
    if not os.path.exists(args.report_dir):
        os.makedirs(args.report_dir)

    # update the parameters.lua file to use the correct CPU socket
    os.system("sed -i 's/tester_socket_id=.*/tester_socket_id=\"" + str(config.getOption('testerSocketId')) + "\"/' " \
            + args.tests_dir + "/prox-configs/parameters.lua")
    os.system("sed -i 's/sut_socket_id=.*/sut_socket_id=\"" + str(config.getOption('sutSocketId')) + "\"/' " \
            + args.tests_dir + "/prox-configs/parameters.lua")

    # Determine which tests to run. These locations are checked in order, the
    # first non-empty result is used:
    # - command line: test names specified as parameters
    # - config file: test names specified in the [general] section, key 'tests'
    # - all tests in the directory specified on the command line with -d
    # - all tests in directory tests/
    tests_to_run = args.test

    if tests_to_run is not None and len(tests_to_run) == 0:
        logging.debug("No test specified on the command line. Checking config file")
        tests_to_run = config.getOption('tests')
        if tests_to_run is not None:
            tests_to_run = tests_to_run.split(',')

    if tests_to_run is None:
        logging.debug("No test specified in the config file. Running all tests from " + args.tests_dir)
        tests_to_run = sorted(all_tests.keys())

    logging.debug("Tests to run: '%s'", "', '".join(tests_to_run))

    test_summaries = []
    for test in tests_to_run:
        if test not in all_tests.keys():
            logging.error("Test '%s' not found. Use the '-l' command line parameter, possibly with '-d' to see the list of available tests.", test)
            continue

        logging.info("Loading test suite %s", test)

        # Load test script directly from disk
        test_module = imp.load_source(test, all_tests[test])

        # Get all classes defined in test_module. Filter out imported classes and
        # classes that are not derived from DATSTest.
        test_classes = [c[1] for c in inspect.getmembers(test_module, inspect.isclass)]
        test_classes = [c for c in test_classes if c.__module__ == test_module.__name__]
        test_classes = [c for c in test_classes if issubclass(c, TestBase)]

        for test_class in test_classes:
            test = test_class()
            logging.info("Running test %s - %s",
                    test.__class__.__name__, test.short_descr())

            test_results = None
            try:
                test.setup_class()
                test_results = test.run_all_tests()
                test.teardown_class()
                logging.trace('Test results: %s', test_results)
                test_summaries.append(dict(test=test, results=test_results))
            except KeyboardInterrupt:
                logging.error("Test run interrupted by keyboard. Generating partial report.")
                test_summaries.append(dict(test=test, results=Exception('Test run interrupted by user')))
                break
            except IOError, ex:
                logging.error("I/O error ({0}): {1}: {2}".format(ex.errno, ex.filename, ex.strerror))
                test_results = ex
            except Exception, ex:
                logging.error(ex)
                logging.debug("Exception: %s", traceback.format_exc())

    logging.info("--------------------------------------------------------------------------------")
    logging.info("Test summary")
    logging.info("--------------------------------------------------------------------------------")
    for summary in test_summaries:
        if 'test' in summary:
            test = summary['test']
            logging.info("%s: %s", test.short_descr(), test.kpi())
        else:
            logging.info("%s: %s", str(test['name']), str(test['kpi']))
    logging.info("--------------------------------------------------------------------------------")

    # Generate reStructuredText summary
    summary_fh = open(args.report_dir + '/' + 'summary.rst', 'w')
    summary_fh.write('.. role:: problematic\n\n')
    summary_fh.write(rst.section('Dataplane Characterization Report', '#', True))
    summary_fh.write("This report was generated by DATS v" + __version__ + " (Dataplane Automated Testing System).\n\n")

    summ_table = [['Test Name', 'KPI']]
    for summary in test_summaries:
        if 'test' not in summary:
            continue

        test = summary['test']
        # The backslash-escaped space allows correct internal link generation,
        # even when a test name contains < or >.
        kpi = None
        if isinstance(summary['results'], Exception):
            kpi = ':problematic:`Error running test`'
        else:
            kpi = test.kpi()
        summ_table.append(['`' + test.short_descr() + '\\ `_', kpi])

    summary_fh.write(rst.section('Executed tests', '*', True))
    summary_fh.write(rst.simple_table(summ_table))
    summary_fh.write("The tolerated packet loss for these tests was {:g}%.\n\n".format(float(config.getOption('toleratedLoss'))))

    summary_fh.write(rst.section('System Under Test information', '*', True))
    summary_fh.write(rst.simple_table(sut_information_hw))
    summary_fh.write(rst.simple_table(sut_information_sw))

    summary_fh.write(rst.section('Test Details', '*', True))
    test_id = 0
    logging.debug("All test results: %s", test_summaries)
    for summary in test_summaries:
        if 'test' in summary:
            test = summary['test']

            summary_fh.write(rst.section(test.short_descr(), '='))

            # Double newlines in description for proper paragraph formatting
            summary_fh.write(rst.section('Description', '-'))
            summary_fh.write(test.long_descr().replace('\n', '\n\n'))
            summary_fh.write('\n\n')

            report_prefix = 't' + str(test_id) + '_' + re.sub('[^a-zA-Z0-9]', '_', test.__module__) + '_'
            summary_fh.write(rst.section('Result', '-'))
            if isinstance(summary['results'], Exception):
                summary_fh.write('**Error while running test:** {}\n\n'.format(str(summary['results'])))
            else:
                summary_fh.write(test.generate_report(summary['results'], report_prefix, args.report_dir + '/'))
    summary_fh.close()


    csv_file = open(args.report_dir + '/' + 'data.csv', 'w')
    for summary in test_summaries:
        if 'test' in summary:
            test = summary['test']
            csv_file.write(test.short_descr() + "\n")
            if not isinstance(summary['results'], Exception):
                csv_file.write(test.generate_csv(summary['results']))
    csv_file.close()

    json_file = open(args.report_dir + '/' + 'summary.json', 'w')
    results_dict = dict()
    for summary in test_summaries:
        if 'test' in summary:
            test = summary['test']
            if not isinstance(summary['results'], Exception):
                results_dict[test.short_descr()] = test.generate_json(summary['results'])
    json_file.write(json.dumps(results_dict))
    json_file.close()

    # TODO More output formats
    os.system('rst2html ' + args.report_dir + '/' + 'summary.rst ' + args.report_dir + '/' + 'summary.html')
    os.system('rst2pdf -q ' + args.report_dir + '/' + 'summary.rst ' + args.report_dir + '/' + 'summary.pdf')


    logging.info("Report generated in %s", args.report_dir)

    ### Flush buffer to logfile
    logging.shutdown()


if __name__ == '__main__':
    main()
