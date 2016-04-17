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
        while prox is None:
            time.sleep(1)
            try:
                prox = self.connect_prox()
            except:
                pass
            if self._err == True:
                raise Exception(self._err_str)
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
