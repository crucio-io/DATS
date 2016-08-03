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

import select
from time import sleep
import logging
import array

class prox(object):
    def __init__(self, prox_socket):
        """ creates new prox instance """
        self._sock = prox_socket
        # sleep(1)
        # self.put_data("tot ierrors tot\n")
        # recv = self.get_data()
        self._pkt_dumps = []

    def get_socket(self):
        """ get the socket connected to the remote instance """
        return self._sock

    def get_data(self, pkt_dump_only=False, timeout=1):
        """ read data from the socket """
        # This method behaves slightly differently depending on whether it is
        # called to read the response to a command (pkt_dump_only = 0) or if
        # it is called specifically to read a packet dump (pkt_dump_only = 1).
        #
        # Packet dumps look like:
        #   pktdump,<port_id>,<data_len>\n
        #   <packet contents as byte array>\n
        # This means the total packet dump message consists of 2 lines instead
        # of 1 line.
        #
        # - Response for a command (pkt_dump_only = 0):
        #   1) Read response from the socket until \n (end of message)
        #   2a) If the response is a packet dump header (starts with "pktdump,"):
        #     - Read the packet payload and store the packet dump for later
        #       retrieval.
        #     - Reset the state and restart from 1). Eventually state 2b) will
        #       be reached and the function will return.
        #   2b) If the response is not a packet dump:
        #     - Return the received message as a string
        #
        # - Explicit request to read a packet dump (pkt_dump_only = 1):
        #   - Read the dump header and payload
        #   - Store the packet dump for later retrieval
        #   - Return True to signify a packet dump was successfully read
        ret_str = None
        dat = ""
        done = 0
        while done == 0:
            # recv() is blocking, so avoid calling it when no data is waiting.
            ready = select.select([self._sock], [], [], timeout)
            if ready[0]:
                logging.debug("Reading from socket")
                dat = self._sock.recv(256)
                ret_str = ""
            else:
                logging.debug("No data waiting on socket")
                done = 1
            logging.trace("Iterating over input buffer (%d octets)", len(dat))

            i = 0
            while i < len(dat) and (done == 0):
                if dat[i] == '\n':
                    # Terminating \n for a string reply encountered.
                    if ret_str.startswith('pktdump,'):
                        logging.trace("Packet dump header read: [%s]", ret_str)
                        # The line is a packet dump header. Parse it, read the
                        # packet payload, store the dump for later retrieval.
                        # Skip over the packet dump and continue processing: a
                        # 1-line response may follow the packet dump.
                        _, port_id, data_len = ret_str.split(',', 2)
                        port_id, data_len = int(port_id), int(data_len)

                        data_start = i + 1      # + 1 to skip over \n
                        data_end = data_start + data_len
                        pkt_payload = array.array('B', map(ord, dat[data_start:data_end]))
                        pkt_dump = PacketDump(port_id, data_len, pkt_payload)
                        self._pkt_dumps.append(pkt_dump)

                        # Reset state. Increment i with payload length and add
                        # 1 for the trailing \n.
                        ret_str = ""
                        i += data_len + 1

                        if pkt_dump_only:
                            # Return boolean instead of string to signal
                            # successful reception of the packet dump.
                            logging.trace("Packet dump stored, returning")
                            ret_str = True
                            done = 1
                    else:
                        # Regular 1-line message. Stop reading from the socket.
                        logging.trace("Regular response read")
                        done = 1
                else:
                    ret_str += dat[i]

                i = i + 1

        logging.debug("Received data from socket: [%s]", ret_str)
        return ret_str

    def put_data(self, to_send):
        """ send data to the remote intance """
        logging.debug("Sending data to socket: [%s]", to_send.rstrip('\n'))
        self._sock.sendall(to_send)

    def get_packet_dump(self):
        """ get the next packet dump """
        if len(self._pkt_dumps):
            return self._pkt_dumps.pop(0)
        else:
            return None

    def stop_all_reset(self):
        """ stop the remote instance and reset stats """
        logging.debug("Stop all and reset stats")
        self.stop_all()
        self.reset_stats()

    def stop_all(self):
        """ stop all cores on the remote instance """
        logging.debug("Stop all")
        self.put_data("stop all\n")
        sleep(3)

    def stop(self, cores, task=-1):
        """ stop specific cores on the remote instace """
        logging.debug("Stopping cores %s", cores)
        task_string = "" if task == -1 else " {}".format(task)
        self.put_data("stop " + str(cores)[1:-1].replace(" ", "") + task_string + "\n")
        sleep(3)

    def start_all(self):
        """ start all cores on the remote instance """
        logging.debug("Start all")
        self.put_data("start all\n")
        #sleep(1)

    def start(self, cores):
        """ start specific cores on the remote instance """
        logging.debug("Starting cores %s", cores)
        self.put_data("start " + str(cores)[1:-1].replace(" ", "") + "\n")
        sleep(3)

    def reset_stats(self):
        """ reset the statistics on the remote instance """
        logging.debug("Reset stats")
        self.put_data("reset stats\n")
        sleep(1)

    def set_pkt_size(self, cores, pkt_size):
        """ set the packet size to generate on the remote instance """
        logging.debug("Set packet size for core(s) %s to %d", cores, pkt_size)
        for core in cores:
            self.put_data("pkt_size " + str(core) + " 0 " + str(pkt_size - 4) + "\n")
        sleep(1)

    def set_value(self, cores, offset, value, length):
        """ set value on the remote instance """
        logging.debug("Set value for core(s) %s to '%s' (length %d), offset %d", cores, value, length, offset)
        for core in cores:
            self.put_data("set value " + str(core) + " 0 " + str(offset) + " " + str(value) + " " + str(length) + "\n")

    def reset_values(self, cores):
        """ reset values on the remote instance """
        logging.debug("Set value for core(s) %s", cores)
        for core in cores:
            self.put_data("reset values " + str(core) + " 0\n")

    def set_speed(self, cores, speed):
        """ set speed on the remote instance """
        logging.debug("Set speed for core(s) %s to %g", cores, speed)
        for core in cores:
            self.put_data("speed " + str(core) + " 0 " + str(speed) + "\n")

    def slope_speed(self, cores_speed, duration, n_steps=0):
        """will start to increase speed from 0 to N where N is taken from
        a['speed'] for each a in cores_speed"""
        cur_speed = []
        speed_delta = []
        # by default, each step will take 0.5 sec
        if n_steps == 0:
            n_steps = duration*2

        step_duration = float(duration)/n_steps
        for a in cores_speed:
            speed_delta.append(float(a['speed'])/n_steps)
            cur_speed.append(0)

        cur_step = 0
        while cur_step < n_steps:
            sleep(step_duration)
            idx = 0
            for a in cores_speed:
                # for last step to avoid any rounding issues from
                # interpolatin, set speed directly
                if cur_step + 1 == n_steps:
                    cur_speed[idx] = a['speed']
                else:
                    cur_speed[idx] = cur_speed[idx] + speed_delta[idx]

                self.set_speed(a['cores'], cur_speed[idx])
                idx = idx + 1
            cur_step = cur_step + 1

    def set_pps(self, cores, pps, pkt_size):
        """ set packets per second for specific cores on the remote instance """
        logging.debug("Set packets per sec for core(s) %s to %g%% of line rate (packet size: %d)", cores, pps, pkt_size)
        # speed in percent of line-rate
        speed = float(pps)/(1250000000/(pkt_size + 20))
        for core in cores:
            self.put_data("speed " + str(core) + " 0 " + str(speed) + "\n")

    def lat_stats(self, cores, task=0):
        """Get the latency statistics from the remote system"""
        lat_min = [0 for e in range(255)]
        lat_max = [0 for e in range(255)]
        lat_avg = [0 for e in range(255)]
        for core in cores:
            self.put_data("lat stats " + str(core) + " " + str(task) + " " +  "\n")
            ret = self.get_data().split(",")
            lat_min[core] = int(ret[0])
            lat_max[core] = int(ret[1])
            lat_avg[core] = int(ret[2])
        return lat_min, lat_max, lat_avg

    def hz(self):
        self.put_data("tot stats\n")
        recv = self.get_data()
        hz = int(recv.split(",")[3])
        return hz

    # Deprecated
    def rx_stats(self, cores, task=0):
        return self.core_stats(cores, task)

    def core_stats(self, cores, task=0):
        """Get the receive statistics from the remote system"""
        rx = tx = drop = tsc = 0
        for core in cores:
            self.put_data("core stats {} {}\n".format(core, task))
            ret = self.get_data().split(",")
            rx += int(ret[0])
            tx += int(ret[1])
            drop += int(ret[2])
            tsc = int(ret[3])
        return rx, tx, drop, tsc

    def port_stats(self, ports):
        """get counter values from a specific port"""
        tot_result = [0] * 12
        for port in ports:
            self.put_data("port_stats {}\n".format(port))
            ret = map(int, self.get_data().split(","))
            tot_result = map(sum, zip(tot_result, ret))
        return tot_result

    def tot_stats(self):
        """Get the total statistics from the remote system"""
        self.put_data("tot stats\n")
        recv = self.get_data()
        tot_rx = int(recv.split(",")[0])
        tot_tx = int(recv.split(",")[1])
        tsc = int(recv.split(",")[2])
        hz = int(recv.split(",")[3])
        return tot_rx, tot_tx, tsc

    def tot_ierrors(self):
        """Get the total ierrors from the remote system"""
        self.put_data("tot ierrors tot\n")
        recv = self.get_data()
        tot_ierrors = int(recv.split(",")[0])
        tsc = int(recv.split(",")[0])
        return tot_ierrors, tsc

    def set_count(self, count, cores):
        """Set the number of packets to send on the specified core"""
        for core in cores:
            self.put_data("count {} 0 {}\n".format(core, count))

    def dump_rx(self, core_id, task_id=0, count=1):
        """Activate dump on rx on the specified core"""
        logging.debug("Activating dump on RX for core %d, task %d, count %d", core_id, task_id, count)
        self.put_data("dump_rx {} {} {}\n".format(core_id, task_id, count))
        sleep(1.5)     # Give PROX time to set up packet dumping



class PacketDump(object):
    def __init__(self, port_id, data_len, payload):
        assert len(payload) == data_len, "Packet dump has specified length {}, but payload is {} bytes long".format(data_len, len(payload))

        self._port_id = port_id
        self._data_len = data_len
        self._payload = payload

    def port_id(self):
        """Get the port id of the packet dump"""
        return self._port_id

    def data_len(self):
        """Get the length of the data received"""
        return self._data_len

    def payload(self, start=None, end=None):
        """Get part of the payload as a list of ordinals.

        Returns a list of byte values, matching the contents of the packet dump.
        Optional start and end parameters can be specified to retrieve only a
        part of the packet contents.

        The number of elements in the list is equal to end - start + 1, so end
        is the offset of the last character.

        Args:
            start (pos. int): the starting offset in the payload. If it is not
                specified or None, offset 0 is assumed.
            end (pos. int): the ending offset of the payload. If it is not
                specified or None, the contents until the end of the packet are
                returned.

        Returns:
            [int, int, ...]. Each int represents the ordinal value of a byte in
            the packet payload.
        """
        if start is None:
            start = 0

        if end is None:
            end = self._data_len - 1

        # Bounds checking on offsets
        assert start >= 0, "Start offset must be non-negative"
        assert end < self._data_len, "End offset must be less than {}".format(self._data_len)

        # Adjust for splice operation: end offset must be 1 more than the offset
        # of the last desired character.
        end += 1

        return self._payload[start:end]

