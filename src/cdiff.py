#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
View colored diff in unified-diff format or side-by-side mode with auto pager.
Requires Python (>= 2.5.0) and less.

See demo at homepage: https://github.com/ymattw/cdiff
"""

import sys
import os
import re
import difflib


COLORS = {
    'reset'         : '\x1b[0m',
    'underline'     : '\x1b[4m',
    'reverse'       : '\x1b[7m',
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

    def __init__(self, hunk_header, old_addr, new_addr):
        self._hunk_header = hunk_header
        self._old_addr = old_addr   # tuple (start, offset)
        self._new_addr = new_addr   # tuple group (start, offset)
        self._hunk_list = []        # list of tuple (attr, line)

    def get_header(self):
        return self._hunk_header

    def get_old_addr(self):
        return self._old_addr

    def get_new_addr(self):
        return self._new_addr

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
        """Returns a generator"""
        for line in self._headers:
            yield self._markup_header(line)

        yield self._markup_old_path(self._old_path)
        yield self._markup_new_path(self._new_path)

        for hunk in self._hunks:
            yield self._markup_hunk_header(hunk.get_header())
            for old, new, changed in hunk.mdiff():
                if changed:
                    if not old[0]:
                        # The '+' char after \x00 is kept
                        # DEBUG: yield 'NEW: %s %s\n' % (old, new)
                        line = new[1].strip('\x00\x01')
                        yield self._markup_new(line)
                    elif not new[0]:
                        # The '-' char after \x00 is kept
                        # DEBUG: yield 'OLD: %s %s\n' % (old, new)
                        line = old[1].strip('\x00\x01')
                        yield self._markup_old(line)
                    else:
                        # DEBUG: yield 'CHG: %s %s\n' % (old, new)
                        yield self._markup_old('-') + \
                            self._markup_old_mix(old[1])
                        yield self._markup_new('+') + \
                            self._markup_new_mix(new[1])
                else:
                    yield self._markup_common(' ' + old[1])

    def markup_side_by_side(self, width):
        """Returns a generator"""
        def _normalize(line):
            return line.replace('\t', ' '*8).replace('\n', '').replace('\r', '')

        def _fit_width(markup, width, pad=False):
            """str len does not count correctly if left column contains ansi
            color code.  Only left side need to set `pad`
            """
            out = []
            count = 0
            ansi_color_regex = r'\x1b\[(1;)?\d{1,2}m'
            patt = re.compile('^(%s)(.*)' % ansi_color_regex)
            repl = re.compile(ansi_color_regex)

            while markup and count < width:
                if patt.match(markup):
                    out.append(patt.sub(r'\1', markup))
                    markup = patt.sub(r'\3', markup)
                else:
                    # FIXME: utf-8 char broken here
                    out.append(markup[0])
                    markup = markup[1:]
                    count += 1

            if count == width and repl.sub('', markup):
                # stripped: output fulfil and still have ascii in markup
                out[-1] = ansi_code('reset') + colorize('>', 'lightmagenta')
            elif count < width and pad:
                pad_len = width - count
                out.append('%*s' % (pad_len, ''))

            return ''.join(out)

        # Setup line width and number width
        if width <= 0:
            width = 80
        (start, offset) = self._hunks[-1].get_old_addr()
        max1 = start + offset - 1
        (start, offset) = self._hunks[-1].get_new_addr()
        max2 = start + offset - 1
        num_width = max(len(str(max1)), len(str(max2)))
        left_num_fmt = colorize('%%(left_num)%ds' % num_width, 'yellow')
        right_num_fmt = colorize('%%(right_num)%ds' % num_width, 'yellow')
        line_fmt = left_num_fmt + ' %(left)s ' + ansi_code('reset') + \
                right_num_fmt + ' %(right)s\n'

        # yield header, old path and new path
        for line in self._headers:
            yield self._markup_header(line)
        yield self._markup_old_path(self._old_path)
        yield self._markup_new_path(self._new_path)

        # yield hunks
        for hunk in self._hunks:
            yield self._markup_hunk_header(hunk.get_header())
            for old, new, changed in hunk.mdiff():
                if old[0]:
                    left_num = str(hunk.get_old_addr()[0] + int(old[0]) - 1)
                else:
                    left_num = ' '

                if new[0]:
                    right_num = str(hunk.get_new_addr()[0] + int(new[0]) - 1)
                else:
                    right_num = ' '

                left = _normalize(old[1])
                right = _normalize(new[1])

                if changed:
                    if not old[0]:
                        left = '%*s' % (width, ' ')
                        right = right.lstrip('\x00+').rstrip('\x01')
                        right = _fit_width(self._markup_new(right), width)
                    elif not new[0]:
                        left = left.lstrip('\x00-').rstrip('\x01')
                        left = _fit_width(self._markup_old(left), width)
                        right = ''
                    else:
                        left = _fit_width(self._markup_old_mix(left), width, 1)
                        right = _fit_width(self._markup_new_mix(right), width)
                else:
                    left = _fit_width(self._markup_common(left), width, 1)
                    right = _fit_width(self._markup_common(right), width)
                yield line_fmt % {
                    'left_num': left_num,
                    'left': left,
                    'right_num': right_num,
                    'right': right
                }

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

    def _markup_mix(self, line, base_color):
        del_code = ansi_code('reverse') + ansi_code(base_color)
        add_code = ansi_code('reverse') + ansi_code(base_color)
        chg_code = ansi_code('underline') + ansi_code(base_color)
        rst_code = ansi_code('reset') + ansi_code(base_color)
        line = line.replace('\x00-', del_code)
        line = line.replace('\x00+', add_code)
        line = line.replace('\x00^', chg_code)
        line = line.replace('\x01', rst_code)
        return colorize(line, base_color)

    def _markup_old_mix(self, line):
        return self._markup_mix(line, 'red')

    def _markup_new_mix(self, line):
        return self._markup_mix(line, 'green')


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
            # 'common' line occurs before 'old_path' is considered as header
            # too, this happens with `git log -p` and `git show <commit>`
            #
            if Udiff.is_header(stream[0]) or \
                    (Udiff.is_common(stream[0]) and old_path is None):
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
                    a = hunk_header.split()[1].split(',')   # -3 7
                    old_addr = (int(a[0][1:]), int(a[1]))
                    b = hunk_header.split()[2].split(',')   # +3 6
                    new_addr = (int(b[0][1:]), int(b[1]))
                    hunk = Hunk(hunk_header, old_addr, new_addr)

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

    def markup(self, side_by_side=False, width=0):
        """Returns a generator"""
        if side_by_side:
            return self._markup_side_by_side(width)
        else:
            return self._markup_traditional()

    def _markup_traditional(self):
        for diff in self._diffs:
            for line in diff.markup_traditional():
                yield line

    def _markup_side_by_side(self, width):
        for diff in self._diffs:
            for line in diff.markup_side_by_side(width):
                yield line


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
    parser.add_option('-w', '--width', type='int', default=80,
            help='set line width (side-by-side mode only), default is 80')
    opts, args = parser.parse_args()

    if len(args) >= 1:
        diff_hdl = open(args[0], 'r')
    elif sys.stdin.isatty():
        sys.stderr.write('Try --help option for usage\n')
        sys.exit(1)
    else:
        diff_hdl = sys.stdin

    # FIXME: can't use generator for now due to current implementation in parser
    stream = diff_hdl.readlines()
    # Don't let empty diff pass thru
    if not stream:
        sys.exit(0)

    if diff_hdl is not sys.stdin:
        diff_hdl.close()

    if sys.stdout.isatty():
        markup = DiffMarkup(stream)
        color_diff = markup.markup(side_by_side=opts.side_by_side,
                width=opts.width)

        # args stolen fron git source: github.com/git/git/blob/master/pager.c
        pager = subprocess.Popen(['less', '-FRSXK'],
                stdin=subprocess.PIPE, stdout=sys.stdout)
        for line in color_diff:
            pager.stdin.write(line)

        pager.stdin.close()
        pager.wait()
    else:
        # pipe out stream untouched to make sure it is still a patch
        sys.stdout.write(''.join(stream))

    sys.exit(0)

# vim:set et sts=4 sw=4 tw=80:
