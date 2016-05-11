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
