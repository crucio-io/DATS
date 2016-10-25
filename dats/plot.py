#
# Dataplane Automated Testing System
#
# Copyright (c) 2015-2016, Intel Corporation.
# Copyright (c) 2016, Viosoft Corportation.
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

'''
Helper functions to create plots
'''

import os


# First col will be
def bar_plot(table, output_path):
    '''
    Creates a bar plot image for the given table on the given output path
    '''
    if len(table[0]) < 2:
        raise Exception("Need at least 1 col of data to create bar plot")

    # Export table to data file
    data = None
    max_value = 0
    for row in table:
        if not data:
            # First iteration: row contains headers
            data = 'titles '
            for header in row[1:]:
                # Skip first column, it's not an axis label
                data += '"' + str(header) + '" '
            data += '\n'
        else:
            # Data
            data += '"' + str(row[0]) + '" '
            data += str(row[1:])[1:-1].replace(',', '')
            data += '\n'
            max_value = max(row[1:]) if max(row[1:]) > max_value else max_value

    # Write data to temp. file, so gnuplot can pick it up for rendering
    temp_file = open('/tmp/plot.dat', 'w')
    temp_file.write(data)
    temp_file.close()

    gnuplot_script = '''
set style data histograms
set style histogram cluster gap 1
set style fill solid border -1
set boxwidth 1
set yrange [0:{}]
set xlabel "{}"
set ylabel "{}"
set term png
set output "{}"
plot "/tmp/plot.dat" using 2:xtic(1) ti col'''.format(1.15*max_value, table[0][0], table[0][1], output_path)

    for i in range(2, len(table[0])):
        gnuplot_script += ", '' using " + str(i + 1) + " ti col"
    gnuplot_script += "\n"

    gnuplot_file = open("/tmp/gnuplot.script", 'w')
    gnuplot_file.write(gnuplot_script)
    gnuplot_file.close()

    os.system("gnuplot /tmp/gnuplot.script")


def plot_throughput_latency(table, output_path):
    '''
    Creates a bar plot image for the given table on the given output path
    '''
    if len(table[0]) < 2:
        raise Exception("Need at least 1 col of data to create bar plot")

    # Export table to data file
    data = "Metric Throuput Latency"
    data += '\n'
    for row in table:
        # Data
        data_line = str(str(row[0]) + "% " + str(row[1]) + ' ' + str(row[2])).strip()
        if len(data_line) > 3:
            data += data_line
            data += '\n'

    # Write data to temp. file, so gnuplot can pick it up for rendering
    temp_file = open('/tmp/histplot.dat', 'w')
    temp_file.write(data)
    temp_file.close()

    gnuplot_script = '''
reset
set ytics nomirror
set y2tics
set yrange [0:]
set y2range [0:]
set key right
set style fill solid border -1

label1 = "Throughput (Mpps)"
label2 = "Latency (ns)"
set ylabel label1
set y2label label2

set tics font ", 10"

set style data histograms
set output "{}"
set term png
set term png size 800,600

plot '/tmp/histplot.dat' using 2 ti col axis x1y1, '' u 3:xticlabels(1) ti col axis x1y2'''.format(output_path)

    gnuplot_script += "\n"

    gnuplot_file = open("/tmp/gnuplot.script", 'w')
    gnuplot_file.write(gnuplot_script)
    gnuplot_file.close()

    os.system("gnuplot /tmp/gnuplot.script")
