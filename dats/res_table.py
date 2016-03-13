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
