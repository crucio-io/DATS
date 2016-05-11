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

import logging
from time import sleep

import dats.test.passfail


class HandleNoneTest(dats.test.passfail.PassFail):
    """Functional tests of the handle_none mode

    This test suite checks the correctness of the ``handle_none`` mode in
    PROX.
    """

    def setup_class(self):
        """Connect to tester and SUT.
        """
        self._tester = self.get_remote('tester').run_prox_with_config("01_handle_none-gen.cfg", "-e -t")
        # TODO tester.run_prox_with_config should raise an exception on error, so the below if block can be removed
        if (self._tester == None):
            raise IOError("Could not connect to PROX on the tester system")
        else:
            logging.debug("Connected to PROX on Tester")

        self._sut = self.get_remote('sut').run_prox_with_config("01_handle_none-sut.cfg", "-t")
        if (self._sut == None):
            raise IOError("Could not connect to PROX on the SUT")
        else:
            logging.debug("Connected to PROX on SUT")

        self._cores = [1, 2, 3, 4]

    def teardown_class(self):
        """Close connections to the tester and SUT.
        """
        self._tester = None
        self._sut = None


    def reset_remotes(self):
        """Reset the tester and SUT.

        All cores will be stopped, the stats will be reset, the packet size
        will be set to 64 and the speed will be set to 100% line rate.
        """
        for remote in [self._tester, self._sut]:
            remote.stop_all()
            remote.reset_stats()
            remote.set_pkt_size(self._cores, 64)
            remote.set_speed(self._cores, 100)
            remote.set_count(0, self._cores)


    @dats.test.passfail.passfailtest(setup=reset_remotes,teardown=reset_remotes)
    def Forwarding(self):
        """Test packet forwarding on all ports"""
        # Mapping between sending core on the tester (key) and receiving core on the
        # tester (t_rx), receiving core on the SUT (s_rx) and sending core on
        # the SUT (s_tx).
        core_map = {
                1:{'t_rx':2, 's_rx':1, 's_tx':1, 's_mac':[0x77, 0x77, 0x77, 0x00, 0x00, 0x01]},
                2:{'t_rx':1, 's_rx':2, 's_tx':2, 's_mac':[0x77, 0x77, 0x77, 0x00, 0x00, 0x02]},
                3:{'t_rx':4, 's_rx':3, 's_tx':3, 's_mac':[0x77, 0x77, 0x77, 0x00, 0x00, 0x03]},
                4:{'t_rx':3, 's_rx':4, 's_tx':4, 's_mac':[0x77, 0x77, 0x77, 0x00, 0x00, 0x04]},
        }

        for tx_core in sorted(self._cores):
            # The cores must be running for the RX task, so disable all TX
            # (except for the port that is tested) by setting the speed to 0.
            self._tester.set_speed(self._cores, 0)
            self._tester.start_all()
            self._tester.dump_rx(core_map[tx_core]['t_rx'], 1)
            self._tester.set_count(1, [tx_core])
            self._tester.set_speed([tx_core], 100)

            logging.verbose('Sending a packet on tester core %d', tx_core)
            self._sut.start_all()
            sleep(0.5)
            self._tester.stop_all()
            self._sut.stop_all()

            _, t_tx, _, _ = self._tester.rx_stats([tx_core])
            t_rx, _, _, _ = self._tester.rx_stats([core_map[tx_core]['t_rx']], 1)
            self.equal(t_tx, 1, 'Tester core {} must send a single packet'.format(tx_core))
            self.equal(t_rx, 1, '... and tester core {} must receive a single packet'.format(core_map[tx_core]['t_rx']))

            # Test packet contents
            self._tester.get_data(True)
            pkt_dump = self._tester.get_packet_dump()
            port_id, data_len, payload = pkt_dump.port_id(), pkt_dump.data_len(), pkt_dump.payload().tolist()
            logging.debug("Packet dump: port %d, len %d, contents: %s", port_id, data_len, payload)

            self.equal(data_len, 60, "... and packet must be 60 bytes")
            self.cmp(payload[ 0: 6], [0x00, 0x00, 0x01, 0x00, 0x00, 0x01], "    ... and dst MAC must change")
            self.cmp(payload[ 6:12], core_map[tx_core]['s_mac'], "    ... and src MAC must be correct")
            self.cmp(payload[12:14], [0x08, 0x00], "    ... and EtherType must be IPv4")
            self.cmp(payload[14:15], [0x45], "    ... and IP version and IHL must not change")
            self.cmp(payload[15:16], [0x00], "    ... and DSCP and ECN must not change")
            self.cmp(payload[16:18], [0x00, 0x1c], "    ... and total IP length must not change")
            self.cmp(payload[18:20], [0x00, 0x01], "    ... and identification field must not change")
            self.cmp(payload[20:22], [0x00, 0x00], "    ... and flags and fragment offset must not change")
            self.cmp(payload[22:23], [0x40], "    ... and TTL must not change")
            self.cmp(payload[23:24], [0x11], "    ... and protocol must be UDP")
            self.cmp(payload[24:26], [0xf7, 0x7D], "    ... and checksum must be correct")
            self.cmp(payload[26:30], [192, 168, 1, 1], "    ... and src IP must not change")
            self.cmp(payload[30:34], [192, 168, 1, 1], "    ... and dst IP must not change")
            self.cmp(payload[34:36], [0x13, 0x88], "    ... and UDP src port must not change")
            self.cmp(payload[36:38], [0x13, 0x88], "    ... and UDP dst port must not change")
            self.cmp(payload[38:40], [0x00, 0x08], "    ... and UDP length must not change")
            self.cmp(payload[40:42], [0x55, 0x7b], "    ... and UDP checksum must be correct")

            # Test where packets have been handled by the SUT
            for rx_core in sorted(self._cores):
                s_rx, s_tx, _, _ = self._sut.rx_stats([rx_core])
                if rx_core == core_map[tx_core]['s_rx']:
                    self.equal(s_rx, 1, '... and SUT core {} must receive a single packet'.format(rx_core))
                    self.equal(s_tx, 1, '... and SUT core {} must transmit a single packet'.format(rx_core))
                else:
                    self.equal(s_rx, 0, '... and SUT core {} must not receive packets'.format(rx_core))
                    self.equal(s_tx, 0, '... and SUT core {} must not transmit packets'.format(rx_core))


                # Test where the packet has been received by the tester
                # Skip core that's supposed to receive the packet, it has been
                # tested is the previous assertion
                if rx_core == core_map[tx_core]['t_rx']:
                    continue

                t_rx, _, _, _ = self._tester.rx_stats([rx_core], 1)
                self.equal(t_rx, 0, '... and tester core {} must not receive packets'.format(rx_core))

            self.reset_remotes()






