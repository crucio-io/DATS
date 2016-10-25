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

class res_table(object):
    def __init__(self, titles = []):
        self._titles = []
        self._data = []
        self.add_mode = 0 # not set, 1 if add_cols, 2 if add_rows, can't interleave usage
        self.col_count = 0
        if len(titles) != 0:
            self.set_titles(titles)

    def set_title_at(self, col, title):
        """Set the title of the specified column"""
        self._titles[col] = title

    def set_empty_titles(self, count):
        """Insert titles as empty strings"""
        if len(self._titles) != 0 and len(self._titles) != count:
            raise Exception("Trying to set " + str(count) + " titles but have table with " + str(len(self._titles)) + "cols")
        self._titles = []
        i = 0
        while i < count:
            self._titles.append("")
            i = i + 1

    def set_titles(self, titles):
        """Replace all the titles of the tabel"""
        if len(self._titles) != 0 and len(self._titles) != len(titles):
            raise Exception("Trying to set " + str(len(titles)) + " titles but have table with " + str(len(self._titles)) + "cols")
        self._titles = list(titles)

    def add_col(self, col):
        """Add a new column at the end of the table"""
        if self.add_mode == 2:
            raise Exception("Used add_row in the past, can't use both add_col/add_row")
        if len(self._titles) == 0:
            raise Exception("Set titles before adding data")
        if self.col_count == 0:
            cnt = len(col)
            i = 0
            while i < cnt:
                self._data.append([])
                value = col[i]
                self._data[i].append(value)
                i = i + 1
        else:
            if self.col_count == len(self._titles):
                raise Exception("Trying to add more columns than titles")
            if len(self._data) != len(col):
                raise Exception("Length previous colums was " + str(len(self._data)) + " but new col is " + str(len(col)))

            i = 0
            for element in col:
                self._data[i].append(element)
                i = i + 1
        self.add_mode = 1
        self.col_count = self.col_count + 1

    def add_row(self, row):
        """Add a new row below the tabel"""
        if self.add_mode == 1:
            raise Exception("Used add_col in the past, can't use both add_col/add_row")
        if len(row) != len(self._titles):
            raise Exception("Trying to add row with " + str(len(row)) + " elements in table with " + str(len(self._titles)) + " cols")
        self._data.append(row)
        self.add_mode = 2

    def to_csv(self, delim = "; "):
        """Convert the table to a csv string"""
        ret = ""
        first = True
        for title in self._titles:
            if first:
                first = False
            else:
                ret += delim
            ret += title
        ret += "\n"

        for row in self._data:
            first = True
            for element in row:
                if first:
                    first = False
                else:
                    ret += delim
                ret += str(element)
            ret += "\n"
        return ret


    def get_titles(self):
        """Get a list of all titles"""
        return self._titles

    def get_rows(self):
        """Get a list of rows"""
        return self._data

    def get_cols(self):
        """Get a list of columns"""
        ret = []
        i = 0
        while i < len(self._titles):
            col = []
            for row in self._data:
                col.append(row[i])
            i = i + 1
            ret.append(col)
        return ret
