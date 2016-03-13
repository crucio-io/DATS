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
