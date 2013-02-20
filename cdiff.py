#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Term based tool to view **colored**, **incremental** diff in Git/Mercurial/Svn
workspace, given patch or two files, or from stdin, with **side by side** and
**auto pager** support.  Requires python (>= 2.5.0) and ``less``.
"""

META_INFO = {
    'version'     : '0.5.1',
    'license'     : 'BSD-3',
    'author'      : 'Matthew Wang',
    'email'       : 'mattwyl(@)gmail(.)com',
    'url'         : 'https://github.com/ymattw/cdiff',
    'keywords'    : 'colored incremental side-by-side diff',
    'description' : ('View colored, incremental diff in workspace, given patch '
                     'or two files, or from stdin, with side by side and  auto '
                     'pager support')
}

import sys

if sys.hexversion < 0x02050000:
    raise SystemExit("*** Requires python >= 2.5.0")
IS_PY3 = sys.hexversion >= 0x03000000

import re
import subprocess
import errno
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


# Keys for revision control probe, diff and log with diff
VCS_INFO = {
    'Git': {
        'probe' : ['git', 'rev-parse'],
        'diff'  : ['git', 'diff'],
        'log'   : ['git', 'log', '--patch'],
    },
    'Mercurial': {
        'probe' : ['hg', 'summary'],
        'diff'  : ['hg', 'diff'],
        'log'   : ['hg', 'log', '--patch'],
    },
    'Svn': {
        'probe' : ['svn', 'info'],
        'diff'  : ['svn', 'diff'],
        'log'   : ['svn', 'log', '--diff'],
    },
}


def colorize(text, start_color, end_color='reset'):
    return COLORS[start_color] + text + COLORS[end_color]


class Hunk(object):

    def __init__(self, hunk_headers, hunk_meta, old_addr, new_addr):
        self._hunk_headers = hunk_headers
        self._hunk_meta = hunk_meta
        self._old_addr = old_addr   # tuple (start, offset)
        self._new_addr = new_addr   # tuple (start, offset)
        self._hunk_list = []        # list of tuple (attr, line)

    def get_hunk_headers(self):
        return self._hunk_headers

    def get_hunk_meta(self):
        return self._hunk_meta

    def get_old_addr(self):
        return self._old_addr

    def get_new_addr(self):
        return self._new_addr

    def append(self, hunk_line):
        """hunk_line is a 2-element tuple: (attr, text), where attris : '-':
        old, '+': new, ' ': common"""
        self._hunk_list.append(hunk_line)

    def mdiff(self):
        r"""The difflib._mdiff() function returns an interator which returns a
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

    # Following detectors, parse_hunk_meta() and parse_hunk_line() are suppose
    # to be overwritten by derived class.  No is_header() anymore, all
    # non-recognized lines are considered as headers
    #
    def is_old_path(self, line):
        return False

    def is_new_path(self, line):
        return False

    def is_hunk_meta(self, line):
        return False

    def parse_hunk_meta(self, line):
        """Returns a 2-element tuple, each of them is a tuple in form of (start,
        offset)"""
        return None

    def parse_hunk_line(self, line):
        """Returns a 2-element tuple: (attr, text), where attr is: '-': old,
        '+': new, ' ': common"""
        return None

    def is_old(self, line):
        return False

    def is_new(self, line):
        return False

    def is_common(self, line):
        return False

    def is_eof(self, line):
        return False

    def markup_traditional(self):
        """Returns a generator"""
        for line in self._headers:
            yield self._markup_header(line)

        yield self._markup_old_path(self._old_path)
        yield self._markup_new_path(self._new_path)

        for hunk in self._hunks:
            for hunk_header in hunk.get_hunk_headers():
                yield self._markup_hunk_header(hunk_header)
            yield self._markup_hunk_meta(hunk.get_hunk_meta())
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
                            self._markup_mix(old[1], 'red')
                        yield self._markup_new('+') + \
                            self._markup_mix(new[1], 'green')
                else:
                    yield self._markup_common(' ' + old[1])

    def markup_side_by_side(self, width):
        """Returns a generator"""
        wrap_char = colorize('>', 'lightmagenta')

        def _normalize(line):
            return line.replace('\t', ' '*8).replace('\n', '').replace('\r', '')

        def _fit_with_marker(text, markup_fn, width, pad=False):
            """Wrap or pad input pure text, then markup"""
            if len(text) > width:
                return markup_fn(text[:width-1]) + wrap_char
            elif pad:
                pad_len = width - len(text)
                return '%s%*s' % (markup_fn(text), pad_len, '')
            else:
                return markup_fn(text)

        def _fit_with_marker_mix(text, base_color, width, pad=False):
            """Wrap or pad input text which contains mdiff tags, markup at the
            meantime with the markup_fix_fn, note only left side need to set
            `pad`"""
            out = [COLORS[base_color]]
            count = 0
            tag_re = re.compile(r'\x00[+^-]|\x01')

            while text and count < width:
                if text.startswith('\x00-'):    # del
                    out.append(COLORS['reverse'] + COLORS[base_color])
                    text = text[2:]
                elif text.startswith('\x00+'):  # add
                    out.append(COLORS['reverse'] + COLORS[base_color])
                    text = text[2:]
                elif text.startswith('\x00^'):  # change
                    out.append(COLORS['underline'] + COLORS[base_color])
                    text = text[2:]
                elif text.startswith('\x01'):   # reset
                    out.append(COLORS['reset'] + COLORS[base_color])
                    text = text[1:]
                else:
                    # FIXME: utf-8 wchar might break the rule here, e.g.
                    # u'\u554a' takes double width of a single letter, also this
                    # depends on your terminal font.  I guess audience of this
                    # tool never put that kind of symbol in their code :-)
                    #
                    out.append(text[0])
                    count += 1
                    text = text[1:]

            if count == width and tag_re.sub('', text):
                # Was stripped: output fulfil and still has normal char in text
                out[-1] = COLORS['reset'] + wrap_char
            elif count < width and pad:
                pad_len = width - count
                out.append('%s%*s' % (COLORS['reset'], pad_len, ''))
            else:
                out.append(COLORS['reset'])

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
        line_fmt = left_num_fmt + ' %(left)s ' + COLORS['reset'] + \
                right_num_fmt + ' %(right)s\n'

        # yield header, old path and new path
        for line in self._headers:
            yield self._markup_header(line)
        yield self._markup_old_path(self._old_path)
        yield self._markup_new_path(self._new_path)

        # yield hunks
        for hunk in self._hunks:
            for hunk_header in hunk.get_hunk_headers():
                yield self._markup_hunk_header(hunk_header)
            yield self._markup_hunk_meta(hunk.get_hunk_meta())
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
                        right = _fit_with_marker(right, self._markup_new, width)
                    elif not new[0]:
                        left = left.lstrip('\x00-').rstrip('\x01')
                        left = _fit_with_marker(left, self._markup_old, width)
                        right = ''
                    else:
                        left = _fit_with_marker_mix(left, 'red', width, 1)
                        right = _fit_with_marker_mix(right, 'green', width)
                else:
                    left = _fit_with_marker(left, self._markup_common, width, 1)
                    right = _fit_with_marker(right, self._markup_common, width)
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
        return colorize(line, 'lightcyan')

    def _markup_hunk_meta(self, line):
        return colorize(line, 'lightblue')

    def _markup_common(self, line):
        return colorize(line, 'reset')

    def _markup_old(self, line):
        return colorize(line, 'lightred')

    def _markup_new(self, line):
        return colorize(line, 'lightgreen')

    def _markup_mix(self, line, base_color):
        del_code = COLORS['reverse'] + COLORS[base_color]
        add_code = COLORS['reverse'] + COLORS[base_color]
        chg_code = COLORS['underline'] + COLORS[base_color]
        rst_code = COLORS['reset'] + COLORS[base_color]
        line = line.replace('\x00-', del_code)
        line = line.replace('\x00+', add_code)
        line = line.replace('\x00^', chg_code)
        line = line.replace('\x01', rst_code)
        return colorize(line, base_color)


class Udiff(Diff):

    def is_old_path(self, line):
        return line.startswith('--- ')

    def is_new_path(self, line):
        return line.startswith('+++ ')

    def is_hunk_meta(self, line):
        """Minimal valid hunk meta is like '@@ -1 +1 @@', note extra chars might
        occur after the ending @@, e.g. in git log
        """
        return (line.startswith('@@ -') and line.find(' @@') >= 8) or \
               (line.startswith('## -') and line.find(' ##') >= 8)

    def parse_hunk_meta(self, hunk_meta):
        # @@ -3,7 +3,6 @@
        a = hunk_meta.split()[1].split(',')   # -3 7
        if len(a) > 1:
            old_addr = (int(a[0][1:]), int(a[1]))
        else:
            # @@ -1 +1,2 @@
            old_addr = (int(a[0][1:]), 0)

        b = hunk_meta.split()[2].split(',')   # +3 6
        if len(b) > 1:
            new_addr = (int(b[0][1:]), int(b[1]))
        else:
            # @@ -0,0 +1 @@
            new_addr = (int(b[0][1:]), 0)

        return (old_addr, new_addr)

    def parse_hunk_line(self, line):
        return (line[0], line[1:])

    def is_old(self, line):
        """Exclude old path and header line from svn log --diff output, allow
        '----' likely to see in diff from yaml file
        """
        return line.startswith('-') and not self.is_old_path(line) and \
                not re.match(r'^-{5,}$', line.rstrip())

    def is_new(self, line):
        return line.startswith('+') and not self.is_new_path(line)

    def is_common(self, line):
        return line.startswith(' ')

    def is_eof(self, line):
        # \ No newline at end of file
        # \ No newline at end of property
        return line.startswith(r'\ No newline at end of')


class PatchStream(object):

    def __init__(self, diff_hdl):
        self._diff_hdl = diff_hdl
        self._stream_header_size = 0
        self._stream_header = []

        # Test whether stream is empty by read 1 line
        line = self._diff_hdl.readline()
        if not line:
            self._is_empty = True
        else:
            self._stream_header.append(line)
            self._stream_header_size += 1
            self._is_empty = False

    def is_empty(self):
        return self._is_empty

    def read_stream_header(self, stream_header_size):
        """Returns a small chunk for patch type detect, suppose to call once"""
        for i in range(1, stream_header_size):
            line = self._diff_hdl.readline()
            if not line:
                break
            self._stream_header.append(line)
            self._stream_header_size += 1
        return self._stream_header

    def __iter__(self):
        for line in self._stream_header:
            yield line
        for line in self._diff_hdl:
            yield line


class DiffParser(object):

    def __init__(self, stream):
        """Detect Udiff with 3 conditions, '## ' uaually indicates svn property
        changes in output from `svn log --diff`
        """
        self._stream = stream

        flag = 0
        for line in self._stream.read_stream_header(100):
            line = decode(line)
            if line.startswith('--- '):
                flag |= 1
            elif line.startswith('+++ '):
                flag |= 2
            elif line.startswith('@@ ') or line.startswith('## '):
                flag |= 4
            if (flag & 7) == 7:
                self._type = 'udiff'
                break
        else:
            raise RuntimeError('unknown diff type')

    def get_diff_generator(self):
        try:
            return self._parse()
        except (AssertionError, IndexError):
            raise RuntimeError('invalid patch format')

    def _parse(self):
        """parse all diff lines, construct a list of Diff objects"""
        if self._type == 'udiff':
            difflet = Udiff(None, None, None, None)
        else:
            raise RuntimeError('unsupported diff format')

        diff = Diff([], None, None, [])
        headers = []

        for line in self._stream:
            line = decode(line)

            if difflet.is_old_path(line):
                # FIXME: '--- ' breaks here, need to probe next 3 lines
                if diff._old_path and diff._new_path and len(diff._hunks) > 0:
                    # One diff constructed
                    yield diff
                    diff = Diff([], None, None, [])
                diff = Diff(headers, line, None, [])
                headers = []

            elif difflet.is_new_path(line):
                diff._new_path = line

            elif difflet.is_hunk_meta(line):
                hunk_meta = line
                old_addr, new_addr = difflet.parse_hunk_meta(hunk_meta)
                hunk = Hunk(headers, hunk_meta, old_addr, new_addr)
                headers = []
                diff._hunks.append(hunk)

            elif len(diff._hunks) > 0 and (difflet.is_old(line) or \
                    difflet.is_new(line) or difflet.is_common(line)):
                diff._hunks[-1].append(difflet.parse_hunk_line(line))

            elif difflet.is_eof(line):
                # ignore
                pass

            else:
                # All other non-recognized lines are considered as headers or
                # hunk headers respectively
                #
                headers.append(line)

        if headers:
            raise RuntimeError('dangling header(s):\n%s' % ''.join(headers))

        # Validate and yield the last patch set
        assert diff._old_path is not None
        assert diff._new_path is not None
        assert len(diff._hunks) > 0
        assert len(diff._hunks[-1]._hunk_meta) > 0
        yield diff


class DiffMarkup(object):

    def __init__(self, stream):
        self._diffs = DiffParser(stream).get_diff_generator()

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


def markup_to_pager(stream, opts):
    markup = DiffMarkup(stream)
    color_diff = markup.markup(side_by_side=opts.side_by_side,
            width=opts.width)

    # args stolen fron git source: github.com/git/git/blob/master/pager.c
    pager = subprocess.Popen(['less', '-FRSX'],
            stdin=subprocess.PIPE, stdout=sys.stdout)
    try:
        for line in color_diff:
            pager.stdin.write(line.encode('utf-8'))
    except KeyboardInterrupt:
        pass

    pager.stdin.close()
    pager.wait()


def check_command_status(arguments):
    """Return True if command returns 0."""
    try:
        return subprocess.call(
            arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
    except OSError:
        return False


def revision_control_diff():
    """Return diff from revision control system."""
    for _, ops in VCS_INFO.items():
        if check_command_status(ops['probe']):
            return subprocess.Popen(ops['diff'], stdout=subprocess.PIPE).stdout


def revision_control_log():
    """Return log from revision control system."""
    for _, ops in VCS_INFO.items():
        if check_command_status(ops['probe']):
            return subprocess.Popen(ops['log'], stdout=subprocess.PIPE).stdout


def decode(line):
    """Decode UTF-8 if necessary."""
    try:
        return line.decode('utf-8')
    except AttributeError:
        return line


def main():
    import optparse

    supported_vcs = sorted(VCS_INFO.keys())

    usage = """
  %prog [options]
  %prog [options] <patch>
  %prog [options] <file1> <file2>"""
    parser = optparse.OptionParser(usage=usage,
            description=META_INFO['description'],
            version='%%prog %s' % META_INFO['version'])
    parser.add_option('-s', '--side-by-side', action='store_true',
            help='show in side-by-side mode')
    parser.add_option('-w', '--width', type='int', default=80, metavar='N',
            help='set text width (side-by-side mode only), default is 80')
    parser.add_option('-l', '--log', action='store_true',
            help='show diff log from revision control')
    parser.add_option('-c', '--color', default='auto', metavar='X',
            help='colorize mode "auto" (default), "always", or "never"')
    opts, args = parser.parse_args()

    if opts.log:
        diff_hdl = revision_control_log()
        if not diff_hdl:
            sys.stderr.write(('*** Not in a supported workspace, supported '
                              'are: %s\n') % ', '.join(supported_vcs))
            return 1
    elif len(args) > 2:
        parser.print_help()
        return 1
    elif len(args) == 2:
        diff_hdl = subprocess.Popen(['diff', '-u', args[0], args[1]],
                stdout=subprocess.PIPE).stdout
    elif len(args) == 1:
        if IS_PY3:
            # Python3 needs the newline='' to keep '\r' (DOS format)
            diff_hdl = open(args[0], mode='rt', newline='')
        else:
            diff_hdl = open(args[0], mode='rt')
    elif sys.stdin.isatty():
        diff_hdl = revision_control_diff()
        if not diff_hdl:
            sys.stderr.write(('*** Not in a supported workspace, supported '
                              'are: %s\n\n') % ', '.join(supported_vcs))
            parser.print_help()
            return 1
    else:
        diff_hdl = sys.stdin

    stream = PatchStream(diff_hdl)

    # Don't let empty diff pass thru
    if stream.is_empty():
        return 0

    if opts.color == 'always' or (opts.color == 'auto' and sys.stdout.isatty()):
        try:
            markup_to_pager(stream, opts)
        except IOError:
            e = sys.exc_info()[1]
            if e.errno == errno.EPIPE:
                pass
    else:
        # pipe out stream untouched to make sure it is still a patch
        for line in stream:
            sys.stdout.write(decode(line))

    if diff_hdl is not sys.stdin:
        diff_hdl.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())

# vim:set et sts=4 sw=4 tw=80:
