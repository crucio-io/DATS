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
