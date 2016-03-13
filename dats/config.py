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

# This module loads the specified config file and provides access to the
# values specified.
#
# Default values are provided when an option is missing in the config file.

import ConfigParser


# Mapping between configuration dict keys and configuration file sections/keys
configurationOptions = (
    # dict key          section     key          Default value
    ( 'pktSizes',       'general',  'pkt_sizes', '64,128,256,512,1024,1280,1518' ),
    ( 'tests',          'general',  'tests',     None ),
    ( 'toleratedLoss',  'general',  'tolerated_loss', 0.0),

    ( 'logFile',        'logging',  'file',      'dats.log' ),
    ( 'logFormat',      'logging',  'format',    "%(asctime)-15s %(levelname)-8s %(filename)20s:%(lineno)-3d %(message)s" ),
    ( 'logDateFormat',  'logging',  'datefmt',   None ),
    ( 'logLevel',       'logging',  'level',     'INFO' ),
    ( 'logOverwrite',   'logging',  'overwrite', 1 ),

    ( 'testerIp',       'tester',   'ip',        None ),
    ( 'testerUser',     'tester',   'user',      'root' ),
    ( 'testerDpdkDir',  'tester',   'rte_sdk',   '/root/dpdk' ),
    ( 'testerDpdkTgt',  'tester',   'rte_target', 'x86_64-native-linuxapp-gcc' ),
    ( 'testerProxDir',  'tester',   'prox_dir',  '/root/prox' ),

    ( 'sutIp',          'sut',      'ip',        None ),
    ( 'sutUser',        'sut',      'user',      'root' ),
    ( 'sutDpdkDir',     'sut',      'rte_sdk',   '/root/dpdk' ),
    ( 'sutDpdkTgt',     'sut',      'rte_target', 'x86_64-native-linuxapp-gcc' ),
    ( 'sutProxDir',     'sut',      'prox_dir',  '/root/prox' ),
)


configuration = {}
cmdline_args = None


def set_cmdline_args(args):
    global cmdline_args
    cmdline_args = vars(args)


def parseFile(filename):
    config_parser = ConfigParser.RawConfigParser()
    config_parser.readfp(open(filename))

    for option in configurationOptions:
        if config_parser.has_option(option[1], option[2]):
            configuration[ option[0] ] = config_parser.get(option[1], option[2])
        else:
            configuration[ option[0] ] = option[3]


def getOption(option):
    return configuration[option]

def getArg(arg):
    global cmdline_args
    return cmdline_args[arg]
