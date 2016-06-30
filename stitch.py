#!/usr/bin/env python2.7

#
# Dataplane Automated Testing System
#
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

# ToDo: Group Headers Together at the Top of the report

import sys
import os
import re
import argparse
from shutil import copyfile
from datetime import datetime
from os import path


def add_report(report_path, stitched_report_path, index):
    with open(report_path + "/summary.rst", 'r') as summary_file:
        summary_file_data = summary_file.read()
    summary_file.close()

    for file in os.listdir(report_path):
        if file.endswith(".png"):
            pre, ext = os.path.splitext(file)
            old_image_name = file
            new_image_name = pre + '.' + str(index) + ext
            copyfile(report_path + '/' + old_image_name, stitched_report_path + '/' + new_image_name)
            summary_file_data = summary_file_data.replace(old_image_name, new_image_name)

    # Open and Append to Final
    with open(stitched_report_path + "/summary.rst", "a") as stitched_report:
        if (index > 0):
            stitched_report.write("\n\n\n")
        stitched_report.write(summary_file_data)
    stitched_report.close()


def main():
    parser = argparse.ArgumentParser(
        description="Dataplane Automated Testing System Reports Stitcher")

    parser.add_argument('-r', '--report', default=datetime.now().strftime('dats-stitched-report-%Y%m%d_%H%M%S'),
                        metavar='DIRECTORY', dest='report_dir',
                        help='Where to save the report. A new directory with timestamp in its name is created by default.')

    args = parser.parse_args()

    stitched_report_path = args.report_dir
    if not os.path.exists(stitched_report_path):
        os.makedirs(stitched_report_path)

    p = re.compile('^dats-report-[0-9]{8}[_][0-9]{6}', re.IGNORECASE)
    folders = filter(path.isdir, os.listdir("."))
    index = 0
    for folder in folders:
        if (p.match(folder)):
            print("Stitching Report " + folder + "...")
            add_report(folder, stitched_report_path, index)
            index += 1

    # Convert Final Output
    os.system('rst2pdf ' + stitched_report_path + '/' + 'summary.rst ' + stitched_report_path + '/' + 'summary.pdf')
    os.system('rst2html ' + stitched_report_path + '/' + 'summary.rst ' + stitched_report_path + '/' + 'summary.html')
    print("Reports Stitched in '" + stitched_report_path + "/'")


if __name__ == '__main__':
    sys.exit(main())
