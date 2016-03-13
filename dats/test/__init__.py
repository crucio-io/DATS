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

def get_tests(dir):
    """Returns all DATS tests in the specified directory.

    The DATS test scripts names must start with 'test_' and end in '.py'. Any
    files in the specified directory that don't conform to these requirements
    are omitted from the result.

    Args:
        dir (str): The directory to search.

    Returns:
        {'test1':'path/to/test_test1.py', 'test2':'path/to/test_test2.py', ...}
        A dict with all DATS tests in the specified directory.
        The keys are the test names, which is simply the filename stripped of
        the leading 'test_' and trailing '.py'.
        The values are the corresponding test script paths.
    """
    tests = {}

    for file in os.listdir(dir):
        if not path.isfile(path.join(dir, file)):
            continue

        if file[:5] != 'test_' or file[-3:] != '.py':
            continue

        tests[file[5:-3]] = path.join(dir, file)

    return tests
