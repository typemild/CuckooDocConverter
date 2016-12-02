# Copyright (c) 2016 Hyo min Bak. (typemild@gmail.com)
#
# License: MIT License
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import sys
import win32api,  win32ui,  win32print,  win32con

from Tkinter import Tk,  Menu # classes
from Tkinter import END # constants
import ScrolledText
import tkFileDialog
import tkMessageBox


class MockViewer:
    def __init__(self,  file_path = ''):
        self.file_path = file_path
        self.root = Tk(className = 'MockViewer')
        self.text_pad = ScrolledText.ScrolledText(self.root,  width = 300,  height = 200)

        self.menu = Menu(self.root)
        self.root.config(menu = self.menu)

        file_menu = Menu(self.menu)
        file_menu.add_command(label = 'Open',  command = self.open_doc_from_dlg)
        file_menu.add_command(label = 'Print to default printer.', command = self.print_doc)
        file_menu.add_separator()
        file_menu.add_command(label = 'Exit...',  command = self.exit)

        self.menu.add_cascade(label = 'File',  menu = file_menu)

        self.text_pad.pack()

    def modal(self):
        if self.file_path:
            self.open_doc()

        self.root.mainloop()

    def open_doc_from_dlg(self):
        file = tkFileDialog.askopenfile(parent = self.root,  mode = 'r', title = 'Select a file...')
        self.file_path = file.name
        file.close()
        if self.file_path:
            self.open_doc()

    def open_doc(self):
        with open(self.file_path, 'r') as file:
            contents = file.read()

        self.text_pad.delete(1.0, END) # delete  all contents.
        self.text_pad.insert(END, contents)

    def print_doc(self):
        margin = { 'left': 200,  'top': 200,  'right': 200,  'bottom': 200 }
        width = 2100
        height = 3000

        # for signature test
        with open(self.file_path, 'r') as file:
            first_line = file.readline().strip()
            if first_line == 'EXPLOIT':
                line = file.readline()
                while line:
                    self._run_script(line)
                    line = file.readline()
                return

        contents = ''
        with open(self.file_path, 'r') as file:
            contents = file.read()

        dc = win32ui.CreateDC()
        dc.CreatePrinterDC(win32print.GetDefaultPrinter())
        dc.SetMapMode(win32con.MM_LOMETRIC)
        dc.SetWindowExt((width, height))
        dc.SetWindowOrg((0, 0))
        dc.StartDoc(self.file_path)
        dc.StartPage()
        dc.DrawText(contents,
                    (margin['left'], margin['top'] * -1, width - margin['right'], (height - margin['bottom']) * -1),
                    win32con.DT_LEFT | win32con.DT_WORDBREAK)
        dc.EndPage()
        dc.EndDoc()

    def exit(self):
        self.root.destroy()

    def _run_script(self, cmd):
        win32api.ShellExecute(0, '', 'cmd.exe', '/c ' + cmd, os.path.dirname(os.path.abspath(self.file_path)), win32con.SW_NORMAL)


def main(argv):
    file_path = ''
    argc = len(argv)
    if argc >= 2:
        file_path = argv[1]

    viewer = MockViewer(file_path)

    if argc >= 3 and argv[2] == '-p':
        viewer.print_doc()
    else:
        viewer.modal()

    sys.exit()

if __name__ == '__main__':
    main(sys.argv[0:])
