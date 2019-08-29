#!/usr/bin/env python
#
# Copyright 2019 Scott Wales
#
# Author: Scott Wales <scott.wales@unimelb.edu.au>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from grafanadb.find import find_parse
from grafanadb.cli import pretty_size
import curses
import os
import requests

sort_size = lambda x: x[1]
sort_inode = lambda x: x[2]

class State():
    def __init__(self, window, root_path, find_args):
        self.window = window

        self.path = root_path
        self.row = 0

        self.children = []

        self.sorter = sort_size
        self.reverse = True

        self.find_args = find_args

        self.pad = curses.newpad(1,1)
        self.pad.scrollok(True)
        self.pad_offset = 0

        # Initialise the directory list
        self.chdir('.')


    def chdir(self, path):
        self.path = os.path.normpath(os.path.join(self.path, path))
        self.pad.clear()
        self.row = 0
        self.pad_offset = 0

        self.children = []

        with os.scandir(self.path) as it:
            for entry in it:
                self.find_args['root_inodes'] = [(entry.stat().st_dev, entry.stat().st_ino)]
                r = requests.get("https://accessdev-test.nci.org.au/dusql/du", json=self.find_args)
                r.raise_for_status()
                r = r.json()
                self.children.append([entry.name, r['size'], r['inodes'], entry.is_dir(follow_symlinks=False)])
                self.redraw()

        self.resort()

    def scroll(self, n):
        newrow = self.row + n
        self.row = min(len(self.children), max(0, newrow))

        rows, cols = self.window.getmaxyx()
        rows = rows - 2 # Remove top and bottom header

        if self.row - self.pad_offset < 2: # Before the second row
            self.pad_offset = max(0, self.row - 2)
        if self.row - self.pad_offset > rows - 2: # Past the second to last row
            self.pad_offset = self.row - (rows - 2)


    def redraw(self):
        self.window.erase()
        self.pad.erase()

        rows, cols = self.window.getmaxyx()
        self.pad.resize(1+len(self.children), cols)

        self.window.addnstr(0,0,self.path, cols)
        self.window.addstr(0, cols-1 - 20, f'{"Size":>9s}   {"Inodes":>8s}')

        self.pad.addstr(0, 4, '..')
        for i, (name, size, inodes, isdir) in enumerate(self.children):
            attrs = curses.A_NORMAL
            if isdir:
                attrs = curses.A_BOLD
                name += '/'
            self.pad.addnstr(1 + i, 4, name, cols-4, attrs)
            self.pad.addstr(1 + i, cols-1 - 20, f'{pretty_size(size):>9s}   {inodes:8d}')

        self.pad.addstr(self.row, 2, '>', curses.A_STANDOUT)

        self.window.addnstr(rows - 1, 0, 'q: Exit    s: Sort by size   i: Sort by inodes    r: Reverse Sort', cols, curses.A_STANDOUT)

        self.window.noutrefresh()
        self.pad.noutrefresh(self.pad_offset, 0, 1, 0, rows - 2, cols)
        curses.doupdate()

    def resort(self):
        self.pad.clear()
        self.children = sorted(self.children, key=self.sorter, reverse=self.reverse)
        
    def update(self, command):
        if command == curses.KEY_UP:
            self.scroll(-1)
        elif command == curses.KEY_DOWN:
            self.scroll(1)
        elif command in (curses.KEY_ENTER, curses.KEY_RIGHT, 10, 13):
            if self.row == 0:
                self.chdir('..')
            if self.children[self.row-1][2] > 0 and self.children[self.row-1][3]:
                self.chdir(self.children[self.row-1][0])
        elif command == curses.KEY_LEFT:
            self.chdir('..')
        elif command == ord('s'):
            self.sorter = sort_size
            self.resort()
        elif command == ord('i'):
            self.sorter = sort_inode
            self.resort()
        elif command == ord('r'):
            self.reverse = not self.reverse
            self.resort()

        self.redraw()


def main(stdscr, root, find_args):
    curses.curs_set(0)
    state = State(stdscr, root, find_args)
    state.redraw()

    while 1:
        # Handle input
        c = stdscr.getch()
        if c == ord('q'):
            break
        else:
            state.update(c)


if __name__ == '__main__':
    curses.wrapper(main)