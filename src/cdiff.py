#!/usr/bin/env python

import sys
import os
import re
import difflib


COLORS = {
    'reset'         : '\x1b[0m',
    'red'           : '\x1b[31m',
    'green'         : '\x1b[32m',
    'yellow'        : '\x1b[33m',
    'blue'          : '\x1b[34m',
    'magenta'       : '\x1b[35m',
    'cyan'          : '\x1b[36m',
    'lightred'      : '\x1b[1;31m',
    'lightgreen'    : '\x1b[1;32m',
    'lightyellow'   : '\x1b[1;33m',
    'lightblue'     : '\x1b[1;34m',
    'lightmagenta'  : '\x1b[1;35m',
    'lightcyan'     : '\x1b[1;36m',
}

def ansi_code(color):
    return COLORS.get(color, '')

def colorize(text, start_color, end_color='reset'):
    return ansi_code(start_color) + text + ansi_code(end_color)


class Hunk(object):

    def __init__(self, hunk_header):
        self._hunk_header = hunk_header
        self._hunk_list = []   # 2-element group (attr, line)

    def get_header(self):
        return self._hunk_header

    def append(self, attr, line):
        """attr: '-': old, '+': new, ' ': common"""
        self._hunk_list.append((attr, line))

    def mdiff(self):
        """The difflib._mdiff() function returns an interator which returns a
        tuple: (from line tuple, to line tuple, boolean flag)

        from/to line tuple -- (line num, line text)
            line num -- integer or None (to indicate a context separation)
            line text -- original line text with following markers inserted:
                '\0+' -- marks start of added text
                '\0-' -- marks start of deleted text
                '\0^' -- marks start of changed text
                '\1' -- marks end of added/deleted/changed text

        boolean flag -- None indicates context separation, True indicates
            either "from" or "to" line contains a change, otherwise False.
        """
        return difflib._mdiff(self._get_old_text(), self._get_new_text())

    def _get_old_text(self):
        out = []
        for (attr, line) in self._hunk_list:
            if attr != '+':
                out.append(line)
        return out

    def _get_new_text(self):
        out = []
        for (attr, line) in self._hunk_list:
            if attr != '-':
                out.append(line)
        return out

    def __iter__(self):
        for hunk_line in self._hunk_list:
            yield hunk_line


class Diff(object):

    def __init__(self, headers, old_path, new_path, hunks):
        self._headers = headers
        self._old_path = old_path
        self._new_path = new_path
        self._hunks = hunks

    def markup_traditional(self):
        out = []

        for line in self._headers:
            out.append(self._markup_header(line))

        out.append(self._markup_old_path(self._old_path))
        out.append(self._markup_new_path(self._new_path))

        for hunk in self._hunks:
            out.append(self._markup_hunk_header(hunk.get_header()))
            save_line = ''
            for from_info, to_info, changed in hunk.mdiff():
                if changed:
                    if not from_info[0]:
                        line = to_info[1].strip('\x00\x01')
                        out.append(self._markup_new(line))
                    elif not to_info[0]:
                        line = from_info[1].strip('\x00\x01')
                        out.append(self._markup_old(line))
                    else:
                        out.append(self._markup_old('-') +
                            self._markup_old_mix(from_info[1]))
                        out.append(self._markup_new('+') +
                            self._markup_new_mix(to_info[1]))
                else:
                    out.append(self._markup_common(' ' + from_info[1]))
        return ''.join(out)

    def markup_side_by_side(self, show_number, width):
        """Do not really need to parse the hunks..."""
        return 'TODO: show_number=%s, width=%d' % (show_number, width)

    def _markup_header(self, line):
        return colorize(line, 'cyan')

    def _markup_old_path(self, line):
        return colorize(line, 'yellow')

    def _markup_new_path(self, line):
        return colorize(line, 'yellow')

    def _markup_hunk_header(self, line):
        return colorize(line, 'lightblue')

    def _markup_common(self, line):
        return colorize(line, 'reset')

    def _markup_old(self, line):
        return colorize(line, 'lightred')

    def _markup_new(self, line):
        return colorize(line, 'lightgreen')

    def _markup_mix(self, line, base_color, del_color, add_color, chg_color):
        line = line.replace('\x00-', ansi_code(del_color))
        line = line.replace('\x00+', ansi_code(add_color))
        line = line.replace('\x00^', ansi_code(chg_color))
        line = line.replace('\x01', ansi_code(base_color))
        return colorize(line, base_color)

    def _markup_old_mix(self, line):
        return self._markup_mix(line, 'cyan', 'lightred', 'lightgreen',
                'yellow')

    def _markup_new_mix(self, line):
        return self._markup_mix(line, 'lightcyan', 'lightred', 'lightgreen',
                'lightyellow')


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
                self._type = 'udiff'
                break
        else:
            raise RuntimeError('unknown diff type')

        try:
            self._diffs = self._parse(stream)
        except (AssertionError, IndexError):
            raise RuntimeError('invalid patch format')


    def get_diffs(self):
        return self._diffs

    def _parse(self, stream):
        if self._type == 'udiff':
            return self._parse_udiff(stream)
        else:
            raise RuntimeError('unsupported diff format')

    def _parse_udiff(self, stream):
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
                    hunk = Hunk(stream.pop(0))

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


class DiffMarkup(object):

    def __init__(self, stream):
        self._diffs = DiffParser(stream).get_diffs()

    def markup(self, side_by_side=False, show_number=False, width=0):
        if side_by_side:
            return self._markup_side_by_side(show_number, width)
        else:
            return self._markup_traditional()

    def _markup_traditional(self):
        out = []
        for diff in self._diffs:
            out.append(diff.markup_traditional())
        return out

    def _markup_side_by_side(self, show_number, width):
        """width of 0 or negative means auto detect terminal width"""
        out = []
        for diff in self._diffs:
            out.append(diff.markup_side_by_side(show_number, width))
        return out


if __name__ == '__main__':
    import optparse
    import subprocess

    usage = '''
    %(prog)s [options] [diff]

    View diff (patch) file if given, otherwise read stdin''' % \
            {'prog': os.path.basename(sys.argv[0])}

    parser = optparse.OptionParser(usage)
    parser.add_option('-s', '--side-by-side', action='store_true',
            help=('show in side-by-side mode'))
    parser.add_option('-n', '--number', action='store_true',
            help='show line number')
    parser.add_option('-w', '--width', type='int', default=0,
            help='set line width (side-by-side mode only)')
    opts, args = parser.parse_args()

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

    if sys.stdout.isatty():
        markup = DiffMarkup(stream)
        color_diff = markup.markup(side_by_side=opts.side_by_side,
                show_number=opts.number, width=opts.width)

        # args stolen fron git source: github.com/git/git/blob/master/pager.c
        pager = subprocess.Popen(['less', '-FRSXK'],
                stdin=subprocess.PIPE, stdout=sys.stdout)
        pager.stdin.write(''.join(color_diff))
        pager.stdin.close()
        pager.wait()
    else:
        # pipe out stream untouched to make sure it is still a patch
        sys.stdout.write(''.join(stream))

    sys.exit(0)

# vim:set et sts=4 sw=4 tw=80:
