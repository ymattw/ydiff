#!/usr/bin/env python

import sys
import os
import re


class Hunk(object):

    def __init__(self, hunk_header, old_addr, old_offset, new_addr, new_offset):
        self.__hunk_header = hunk_header
        self.__old_addr = old_addr
        self.__old_offset = old_offset
        self.__new_addr = new_addr
        self.__new_offset = new_offset
        self.__hunk_list = []   # 2-element group (attr, line)

    def get_header(self):
        return self.__hunk_header

    def get_old_addr(self):
        return (self.__old_addr, self.__old_offset)

    def get_new_addr(self):
        return (self.__new_addr, self.__new_offset)

    def append(self, attr, line):
        """attr: '-': old, '+': new, ' ': common"""
        self.__hunk_list.append((attr, line))

    def __iter__(self):
        for hunk_line in self.__hunk_list:
            yield hunk_line


class Diff(object):

    def __init__(self, headers, old_path, new_path, hunks):
        self.__headers = headers
        self.__old_path = old_path
        self.__new_path = new_path
        self.__hunks = hunks

    def view_traditional(self, show_color):
        out = []
        if show_color:
            color = None    # Use default
            end_color = None
        else:
            color = 'none'  # No color
            end_color = 'none'

        for line in self.__headers:
            out.append(self._view_header(line, color, end_color))

        out.append(self._view_old_path(self.__old_path, color, end_color))
        out.append(self._view_new_path(self.__new_path, color, end_color))

        for hunk in self.__hunks:
            out.append(self._view_hunk_header(hunk.get_header(), color,
                end_color))
            for (attr, line) in hunk:
                if attr == '-':
                    out.append(self._view_old(attr+line, color, end_color))
                elif attr == '+':
                    out.append(self._view_new(attr+line, color, end_color))
                else:
                    out.append(self._view_common(attr+line, color, end_color))

        return ''.join(out)

    def view_side_by_side(self, show_color, show_number, width):
        """Do not really need to parse the hunks..."""
        return 'TODO: show_color=%s, show_number=%s, width=%d' % (show_color,
                show_number, width)

    def _view_header(self, line, color=None, end_color=None):
        if color is None:
            color='cyan'
        if end_color is None:
            end_color = 'reset'
        return self.__mark_color(line, color, end_color)

    def _view_old_path(self, line, color=None, end_color=None):
        if color is None:
            color='yellow'
        if end_color is None:
            end_color = 'reset'
        return self.__mark_color(line, color, end_color)

    def _view_new_path(self, line, color=None, end_color=None):
        if color is None:
            color='yellow'
        if end_color is None:
            end_color = 'reset'
        return self.__mark_color(line, color, end_color)

    def _view_hunk_header(self, line, color=None, end_color=None):
        if color is None:
            color='lightblue'
        if end_color is None:
            end_color = 'reset'
        return self.__mark_color(line, color, end_color)

    def _view_old(self, line, color=None, end_color=None):
        if color is None:
            color='red'
        if end_color is None:
            end_color = 'reset'
        return self.__mark_color(line, color, end_color)

    def _view_new(self, line, color=None, end_color=None):
        if color is None:
            color='green'
        if end_color is None:
            end_color = 'reset'
        return self.__mark_color(line, color, end_color)

    def _view_common(self, line, color=None, end_color=None):
        if color is None:
            color='none'
        if end_color is None:
            end_color = 'none'
        return self.__mark_color(line, color, end_color)

    def __mark_color(self, text, start_code, end_code):
        colors = {
                'none'          : '',
                'reset'         : '\x1b[0m',
                'red'           : '\x1b[31m',
                'green'         : '\x1b[32m',
                'yellow'        : '\x1b[33m',
                'blue'          : '\x1b[34m',
                'cyan'          : '\x1b[36m',
                'lightblue'     : '\x1b[1;34m',
            }
        return colors.get(start_code) + text + colors.get(end_code)


class Udiff(Diff):

    @staticmethod
    def is_old_path(line):
        return line.startswith('--- ')

    @staticmethod
    def is_new_path(line):
        return line.startswith('+++ ')

    @staticmethod
    def is_hunk_header(line):
        return line.startswith('@@ -')

    @staticmethod
    def is_old(line):
        return line.startswith('-') and not Udiff.is_old_path(line)

    @staticmethod
    def is_new(line):
        return line.startswith('+') and not Udiff.is_new_path(line)

    @staticmethod
    def is_common(line):
        return line.startswith(' ')

    @staticmethod
    def is_eof(line):
        # \ No newline at end of file
        return line.startswith('\\')

    @staticmethod
    def is_header(line):
        return re.match(r'^[^+@\\ -]', line)


class DiffParser(object):

    def __init__(self, stream):
        for line in stream[:10]:
            if line.startswith('+++ '):
                self.__type = 'udiff'
                break
        else:
            raise RuntimeError('unknown diff type')

        try:
            self.__diffs = self.__parse(stream)
        except (AssertionError, IndexError):
            raise RuntimeError('invalid patch format')


    def get_diffs(self):
        return self.__diffs

    def __parse(self, stream):
        if self.__type == 'udiff':
            return self.__parse_udiff(stream)
        else:
            raise RuntimeError('unsupported diff format')

    def __parse_udiff(self, stream):
        """parse all diff lines here, construct a list of Udiff objects"""
        out_diffs = []
        headers = []
        old_path = None
        new_path = None
        hunks = []
        hunk = None

        while stream:
            if Udiff.is_header(stream[0]):
                if headers and old_path:
                    # Encounter a new header
                    assert new_path is not None
                    assert hunk is not None
                    hunks.append(hunk)
                    out_diffs.append(Diff(headers, old_path, new_path, hunks))
                    headers = []
                    old_path = None
                    new_path = None
                    hunks = []
                    hunk = None
                else:
                    headers.append(stream.pop(0))

            elif Udiff.is_old_path(stream[0]):
                if old_path:
                    # Encounter a new patch set
                    assert new_path is not None
                    assert hunk is not None
                    hunks.append(hunk)
                    out_diffs.append(Diff(headers, old_path, new_path, hunks))
                    headers = []
                    old_path = None
                    new_path = None
                    hunks = []
                    hunk = None
                else:
                    old_path = stream.pop(0)

            elif Udiff.is_new_path(stream[0]):
                assert old_path is not None
                assert new_path is None
                new_path = stream.pop(0)

            elif Udiff.is_hunk_header(stream[0]):
                assert old_path is not None
                assert new_path is not None
                if hunk:
                    # Encounter a new hunk header
                    hunks.append(hunk)
                    hunk = None
                else:
                    # @@ -3,7 +3,6 @@
                    hunk_header = stream.pop(0)

                    addr_info = hunk_header.split()[1]
                    assert addr_info.startswith('-')
                    old_addr = addr_info.split(',')[0]
                    old_offset = addr_info.split(',')[1]

                    addr_info = hunk_header.split()[2]
                    assert addr_info.startswith('+')
                    new_addr = addr_info.split(',')[0]
                    new_offset = addr_info.split(',')[1]

                    hunk = Hunk(hunk_header, old_addr, old_offset, new_addr,
                            new_offset)

            elif Udiff.is_old(stream[0]) or Udiff.is_new(stream[0]) or \
                    Udiff.is_common(stream[0]):
                assert old_path is not None
                assert new_path is not None
                assert hunk is not None
                hunk_line = stream.pop(0)
                hunk.append(hunk_line[0], hunk_line[1:])

            elif Udiff.is_eof(stream[0]):
                # ignore
                stream.pop(0)

            else:
                raise RuntimeError('unknown patch format: %s' % stream[0])

        # The last patch
        if hunk:
            hunks.append(hunk)
        if old_path:
            if new_path:
                out_diffs.append(Diff(headers, old_path, new_path, hunks))
            else:
                raise RuntimeError('unknown patch format after "%s"' % old_path)
        elif headers:
            raise RuntimeError('unknown patch format: %s' % \
                    ('\n'.join(headers)))

        return out_diffs


class DiffViewer(object):

    def __init__(self, stream):
        self.__diffs = DiffParser(stream).get_diffs()

    def view(self, show_color=True, show_number=False, width=0,
            traditional=False):
        if traditional:
            return self.__view_traditional(show_color)
        else:
            return self.__view_side_by_side(show_color, show_number, width)

    def __view_traditional(self, show_color):
        out = []
        for diff in self.__diffs:
            out.append(diff.view_traditional(show_color))
        return out

    def __view_side_by_side(self, show_color, show_number, width):
        """width of 0 or negative means auto detect terminal width"""
        out = []
        for diff in self.__diffs:
            out.append(diff.view_side_by_side(show_color, show_number, width))
        return out


if __name__ == '__main__':
    import optparse
    import subprocess

    usage = '''
    %(prog)s [options] [diff]

    View diff (patch) file if given, otherwise read stdin''' % \
            {'prog': os.path.basename(sys.argv[0])}

    parser = optparse.OptionParser(usage)
    parser.add_option('-c', '--color', metavar='on|off|auto', default='auto',
            help='enforce color' 'on|off|auto, default is auto')
    parser.add_option('-n', '--number', action='store_true',
            help='show line number')
    parser.add_option('-w', '--width', type='int', default=0,
            help='set text width for each side')
    parser.add_option('-t', '--traditional', action='store_true',
            help=('show in traditional format other than default side-by-side '
                  'mode (omit -n, -w)'))
    opts, args = parser.parse_args()

    if opts.color == 'yes':
        show_color = True
    elif opts.color == 'no':
        show_color = False
    elif opts.color == 'auto':
        show_color = sys.stdout.isatty()
    else:
        sys.stderr.write('Invalid color mode, try --help option for usage\n')
        sys.exit(1)

    if opts.width < 0:
        opts.width = 0

    if len(args) >= 1:
        diff_hdl = open(args[0], 'r')
    elif sys.stdin.isatty():
        sys.stderr.write('Try --help option for usage\n')
        sys.exit(1)
    else:
        diff_hdl = sys.stdin

    stream = diff_hdl.readlines()
    if diff_hdl is not sys.stdin:
        diff_hdl.close()

    diffviewer = DiffViewer(stream)
    view = diffviewer.view(show_color=show_color, show_number=opts.number,
            width=opts.width, traditional=opts.traditional)

    if sys.stdout.isatty():
        # args stolen fron git source, see less(1)
        # https://github.com/git/git/blob/master/pager.c
        pager = subprocess.Popen(['less', '-FRSXK'],
                stdin=subprocess.PIPE, stdout=sys.stdout)
        pager.stdin.write(''.join(view))
        pager.stdin.close()
        pager.wait()
    else:
        sys.stdout.write(''.join(view))

    sys.exit(0)

# vim:set et sts=4 sw=4 tw=80:
