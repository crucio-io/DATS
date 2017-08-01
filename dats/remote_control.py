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

import os, os.path as path
import thread
import time
import socket
import logging
import errno

from dats.prox import prox
import dats.config as config


def ssh(user, ip, cmd):
    """Execute ssh command"""
    logging.debug("Command to execute over SSH: '%s'", cmd)
    ssh_options = ""
    ssh_options += "-o StrictHostKeyChecking=no "
    ssh_options += "-o UserKnownHostsFile=/dev/null "
    ssh_options += "-o LogLevel=error "
    running = os.popen("ssh " + ssh_options + " " + user + "@" + ip + " \"" + cmd + "\"")
    ret = {}
    ret['out'] = running.read().strip()
    ret['ret'] = running.close()
    if ret['ret'] is None:
        ret['ret'] = 0

    return ret

def ssh_check_quit(obj, user, ip, cmd):
    ret = ssh(user, ip, cmd)
    if ret['ret'] != 0:
        obj._err = True
        obj._err_str = ret['out']
        exit(-1)

class remote_system:
    def __init__(self, user, ip, dpdk_dir, dpdk_target, prox_dir):
        self._ip          = ip
        self._user        = user
        self._dpdk_dir    = dpdk_dir
        self._dpdk_target = dpdk_target
        self._prox_dir    = prox_dir
        self._dpdk_bind_script = self._dpdk_dir + "/tools/dpdk_nic_bind.py"
        self._err = False
        self._err_str = None

    def run_cmd(self, cmd):
        """Execute command over ssh"""
        return ssh(self._user, self._ip, cmd)

    def mount_hugepages(self, directory="/mnt/huge"):
        """Mount the hugepages on the remote system"""
        self.run_cmd("sudo mkdir -p " + directory)
        self.run_cmd("sudo umount " + directory)
        self.run_cmd("sudo mount -t hugetlbfs nodev " + directory)

    def get_hp_2mb(self):
        ret = self.run_cmd("cat /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages 2>/dev/null")
        if ret['ret'] == 0:
            return ret['out']
        else:
            return 0

    def get_hp_1gb(self):
        ret = self.run_cmd("cat /sys/devices/system/node/node0/hugepages/hugepages-1048576kB/nr_hugepages 2>/dev/null ")
        if ret['ret'] == 0:
            return ret['out']
        else:
            return 0

    def insmod_igb_uio(self):
        self.run_cmd("sudo modprobe uio")
        self.run_cmd("sudo rmmod igb_uio")
        self.run_cmd("sudo insmod " + self._dpdk_dir + "/" + self._dpdk_target + "/kmod/igb_uio.ko")

    def install_dpdk(self, dpdk_tar="dpdk.tar"):
        self.run_cmd("mkdir -p " + "/tmp")
        self.scp(dpdk_tar, "/tmp/")
        self.run_cmd("tar xf /tmp/" + dpdk_tar + " -C " + self._dpdk_dir)
        self.run_cmd("cd " + self._dpdk_dir + "; make install T=" + self._dpdk_target)

    def install_prox(self, prox_tar="prox.tar"):
        self.run_cmd("mkdir -p " + "/tmp")
        self.scp(prox_tar, "/tmp/")
        self.run_cmd("tar xzf /tmp/" + prox_tar + " -C " + self._prox_dir)
        self.run_cmd("cd " + self._prox_dir + "; make")

    def get_ports_niantic(self):
        ret = self.run_cmd("lspci | grep 82599 | cut -d ' ' -f1")['out'].split("\n")
        if len(ret) == 1 and ret[0] == "":
            return []
        return ret

    def get_ports_fortville(self):
        ret = self.run_cmd("lspci | grep X710 | cut -d ' ' -f1")['out'].split("\n")
        if len(ret) == 1 and ret[0] == "":
            return []
        return ret

    def get_port_numa_node(self, pci_address):
        return self.run_cmd("cat /sys/bus/pci/devices/0000\\:" + pci_address + "/numa_node")['out']

    def get_ports(self):
        return self.get_ports_niantic() + self.get_ports_fortville()

    def bind_port(self, pci_address):
        self.run_cmd("sudo python2.7 " + self._dpdk_bind_script + " --bind=igb_uio " +  pci_address)

    def unbind_port(self, pci_address):
        self.run_cmd("sudo python2.7 " + self._dpdk_bind_script + " -u " +  pci_address)

    def port_is_binded(self, pci_address):
        res = self.run_cmd("sudo python2.7 " + self._dpdk_bind_script + " --status | grep " + pci_address)
        return res['out'].find("drv=igb_uio") != -1

    def run_cmd_forked(self, cmd):
        thread.start_new_thread(ssh, (self._user, self._ip, cmd))
        return 0

    def get_core_count(self):
        ret = self.run_cmd("cat /proc/cpuinfo | grep processor | wc -l")['out']
        return int(ret)

    def run_prox(self, prox_args):
        """Run and connect to prox on the remote system """
        # Deallocating a large amout of hugepages takes some time. If a new
        # PROX instance is started immediately after killing the previous one,
        # it might not be able to allocate hugepages, because they are still
        # being freed. Hence the -w switch.
        self.run_cmd("sudo killall -w prox 2>/dev/null")

        prox_cmd = "export TERM=xterm; export RTE_SDK=" + self._dpdk_dir + "; " \
            + "export RTE_TARGET=" + self._dpdk_target + ";" \
            + " cd " + self._prox_dir + "; make HW_DIRECT_STATS=y -j50; sudo " \
            + "./build/prox " + prox_args
        self._err = False
        logging.debug("Starting PROX with command [%s]", prox_cmd)
        thread.start_new_thread(ssh_check_quit, (self, self._user, self._ip, prox_cmd))
        prox = None
        logging.debug("Waiting for PROX to settle")
        
        # try connecting to prox for 120s
        connection_timeout = 120
        while prox is None:
            time.sleep(1)
            connection_timeout -= 1
            try:
                prox = self.connect_prox()
            except:
                pass
            if self._err == True:
                raise Exception(self._err_str)
            if connection_timeout == 0:
                raise Exception("Failed to connect to prox, please check if system " \
                        + self._ip + " accepts connections on port 8474")
        return prox

    def run_prox_with_config(self, configfile, prox_args, sysname="system"):
        """Run prox on the remote system with the given config file"""
        logging.debug("Setting up PROX to run with args '%s' and config file %s", prox_args, configfile)

        # Take config files from subdir prox-configs/ in test script directory
        conf_localpath = path.join(config.getArg('tests_dir'), 'prox-configs', configfile)
        if not path.isfile(conf_localpath):
            raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), conf_localpath)

        conf_remotepath = "/tmp/" + configfile
        logging.debug("Config file local path: '%s', remote name: '%s'", conf_localpath, conf_remotepath)
        self.scp(conf_localpath, conf_remotepath)

        #sock = self.connect_prox()
        sock = self.run_prox(prox_args + " -f " + conf_remotepath)
        if sock == None:
            raise IOError(self.__class__.__name__, "Could not connect to PROX on the {}".format(sysname))
        logging.debug("Connected to PROX on {}".format(sysname))
        return sock

    def connect_prox(self):
        """Connect to the prox instance on the remote system"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self._ip, 8474))
            return prox(sock)
        except:
            raise Exception("Failed to connect to PROX on " + self._ip)
        return None

    def scp(self, local, remote):
        """Copy a file from the local system to the remote system"""
        logging.debug("Initiating SCP: %s -> %s", local, remote)
        cmd = "scp " + local + " " + self._user + "@" + self._ip + ":" + remote
        logging.debug("SCP command: [%s]", cmd)
        running = os.popen(cmd)
        ret = {}
        ret['out'] = running.read().strip()
        ret['ret'] = running.close()
        if ret['ret'] is None:
            ret['ret'] = 0

        logging.debug("SCP status: %d, output: [%s]", ret['ret'], ret['out'])

        return ret

    def copy_extra_config(self, filename):
        logging.debug("Copying extra config file %s", filename)
        local = path.join(config.getArg('tests_dir'), 'prox-configs', filename)
        if not path.isfile(local):
            raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), local)

        remote = "/tmp/" + filename
        logging.debug("Config file local path: '%s', remote name: '%s'", local, remote)
        self.scp(local, remote)

    def get_cpu_topology(self):
        cores = ssh(self._user, self._ip, self._dpdk_dir + "/tools/cpu_layout.py | grep 'cores'")
        sockets = ssh(self._user, self._ip, self._dpdk_dir + "/tools/cpu_layout.py | grep 'sockets'")
        topology = ssh(self._user, self._ip, self._dpdk_dir + "/tools/cpu_layout.py | grep 'Core [0-9]' | tr -s ' '")

        # convert sockets info to a list
        sockets = sockets["out"].split("=")[1].replace("[", "").replace("]", "").replace(" ", "").split(",")
        sockets = map(int, sockets)

        # convert cores info to a list
        cores = cores["out"].split("=")[1].replace("[", "").replace("]", "").replace(" ", "").split(",")
        cores = map(int, cores)

        # convert topolgy info to a dictionary
        topology = topology["out"].split("\n")
        for i in range(0, len(topology)):
            core_map = topology[i].replace("Core", "").replace(" ", "").replace("]", "").split("[")
            core_map[0] = int(core_map[0])
            for j in range(1, len(core_map)):
                core_map[j] = core_map[j].split(",")
                core_map[j] = map(int, core_map[j])
            topology[i] = [core_map[0], core_map[1:]]
        topology = dict(topology)

        # create a map of the CPU topology
        # the structure is as follows:
        # { socket_num : { core_num :[hyperthread_num, hyperthread_num]}}
        topology_map = {}
        for socket in sockets:
            socket_map = {} 
            core_id = 0
            for core in cores:
                socket_map[core_id] = topology[core][socket]
                core_id += 1
            topology_map[socket] = socket_map

        return topology_map

