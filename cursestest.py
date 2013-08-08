import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

import curses
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()

begin_x = 20 ; begin_y = 7
height = 5 ; width = 40
win = curses.newwin(height, width, begin_y, begin_x)

win.addstr("test")
win.refresh()
c = stdscr.getch()

curses.endwin()
curses.nocbreak(); stdscr.keypad(0); curses.echo()