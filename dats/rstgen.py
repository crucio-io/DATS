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

"""
Helper functions to generate reStructuredText.
"""

import logging


def section(title, adornment, overline = False):
    """Generate a section title with the specified adornment.

    Args:
        title (str): The title of the section, *without* terminating \n
        adornment (str): The character used for over/underlining the title
        overline (bool): Whether to overline (True) or just underline (False)

    Returns:
        str. The adorned title.
    """
    result = ''
    line_len = len(title)

    if overline:
        # Inset the title
        line_len += 2
        title = ' ' + title

        result += adornment * line_len
        result += '\n'

    result += title
    result += '\n'

    result += adornment * line_len
    result += '\n\n'

    return result

def simple_table(array, has_hdr = True):
    """Generate a simple table with the contents of array.

    Args:
        array ([[hdr1,hdr2,...], [...],...]): A list of lists containing the
            values to put in the table.
        has_hdr (bool): True if the first list contains the header names of
            the columns. False if the first list contains data.

    Returns:
        str. A simple table in RST format containing the array data.
    """
    result = ''

    logging.trace('Array passed in: %s', array)
    # Calculate max. lengths of each column. RST tables require column
    # alignment.
    col_widths = [0] * len(sorted(array, cmp=lambda x,y: -cmp(len(x), len(y)))[0])
    logging.trace('Initialized col_widths with 0: %s', col_widths)
    for row in array:
        logging.trace('- Adjusting column widths for row %s', row)
        for index in range(len(row)):
            col_widths[index] = max(col_widths[index], len(str(row[index])))
        logging.trace('  New col_widths: %s', col_widths)

    # Draw top border
    for col_width in col_widths:
        result += '=' * col_width
        result += '  '
    result += '\n'

    # Draw table cells, pad every cell with appropriate amount of spaces for
    # correct alignment.
    hdr_border_drawn = False
    for row in array:
        if len(row) > 1:
            for index in range(len(row)):
                result += str(row[index]).ljust(col_widths[index])
                result += '  '
            result += '\n'

            # Draw table header border if needed
            if has_hdr and not hdr_border_drawn:
                for col_width in col_widths:
                    result += '=' * col_width
                    result += '  '
                result += '\n'

            hdr_border_drawn = True
        else:
            result += row[0] + "\n"

            for index in range(len(col_widths)):
                result += '=' * col_widths[index]
                result += '==' if index > 0 else ""
            result += '\n'
            hdr_border_drawn = True

    # Draw bottom border
    for col_width in col_widths:
        result += '=' * col_width
        result += '  '
    result += '\n\n'

    return result

def include(file):
    """Generate an include directive for the specified file.

    Args:
        file (str): Path of the file to include
    """
    # It seems the include directive is disabled for security reasons. Instead
    # of generating a directive, just read the file and return its contents
    # directly instead.

    #result  = '\n'
    #result += '.. include ' + file + '\n'
    #result += '\n'

    result = ''
    fh = open(file)
    result += fh.read()
    fh.close()
    result += '\n'

    return result
