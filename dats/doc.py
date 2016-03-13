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

from os import system
from os import path
from res_table import *

class doc:
    def __init__(self, title):
        self._title = title
        self._elements = []
    def add_fig(self, fig):
        if (path.isfile(fig)):
            self._elements.append([0, fig])
        else:
            raise Exception("Figure " + fig + " does not exist")
    def add_section_title(self, title):
        self._elements.append([1, title])
    def add_table(self, table): # expects to receive a res_table object
        self._elements.append([2, table])
    def add_paragraph(self, text):
        self._elements.append([-1, text])
    def gen_pdf(self, out_path, out_name):
        # Temporarily disable PDF generation. There should be a single PDF for
        # the complete test run instead of 1 PDF per test.
        return

        system("rm -rf ./pdf")
        system("mkdir -p pdf")

        res = ""
        res += "\\documentclass[a4paper,10pt,notitlepage]{article}\n"
        res += "\\title{" + self._title + "}\n"
        res += "\\date{}\n"
        res += "\\usepackage[pdftex]{graphicx}\n"
        res += "\\begin{document}\n"
        res += "\\maketitle\n"
        for a in self._elements:
            if (a[0] == 0):
                system("cp " + a[1] + " "+out_path+" ")
                res += "\\includegraphics[width=\\linewidth]{" + a[1] + "}\n"
            elif (a[0] == 1):
                res += "\\section{"+ a[1] + "}\n"
            elif (a[0] == 2):
                titles = a[1].get_titles()
                res += "\\begin{center}"
                res += "\\begin{tabular}{ |" + (" l |"*len(titles)) + "}\n"
                res += "\\hline\n"

                first = True
                for title in titles:
                    if (first):
                        first = False
                    else:
                        res += " & "
                    res += "\\textbf{" + str(title) + "}"
                res += "\\\\\n"
                res += "\\hline\n"

                first = True
                res += str()

                for row in a[1].get_rows():
                    first = True
                    for el in row:
                        if (first):
                            first = False
                        else:
                            res += " & "
                        res += str(el)
                    res += "\\\\\n"
                res += "\\hline\n"
                res += "\\end{tabular}\n"
                res += "\\end{center}"
            else:
                res += a[1] + "\n\n"

        res += "\\end{document}\n"

        if (out_name[-4:] == ".pdf"):
            out_name = out_name[:-4]

        f = open(out_path + "/" + out_name + ".tex", 'w')
        f.write(res)
        f.close()
        system("cd "+out_path+"/; latexmk -pdf "+out_name+".tex;")
    def gen_html(self, out_path, out_name):

        res = ""
        res += "<html>"
        res += " <h1>" + self._title + "</h1>"
        for a in self._elements:
            if (a[0] == 0):
                system("cp " + a[1] + " "+out_path+"/")
                res += "<par><center><img src='" + a[1] + "'/></center></par>"
            elif (a[0] == 1):
                res += "<h2>"+ a[1] + "</h2>"
            elif (a[0] == 2):
                res += "<table border=\"1\" width=\"100%\">"

                titles = a[1].get_titles()
                res += "<tr>"
                for title in titles:
                    res += "<td><b>" + str(title) + "</b></td>"
                res += "</tr>"


                for row in a[1].get_rows():
                    res += "<tr>"
                    for el in row:
                        res += "<td>" + str(el) + "</td>"
                    res += "</tr>"

                res += "</table>"
            else:
                res += "<par>" + a[1] + "</par></br>"

        res += "</html>"
        f = open(out_path + "/" + out_name, 'w')
        f.write(res)
        f.close()
