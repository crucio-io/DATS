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

def calc_line_rate(arr, n_ports = 1):
    ret = []
    for a in arr:
        ret.append(float(1250000000*n_ports)/(a+20) / 1000000)
    return ret;

def line_rate_to_pps(pkt_size, n_ports):
    # FIXME Don't hardcode 10Gb/s
    return n_ports * float(10000000000 / 8) / (pkt_size + 20)
