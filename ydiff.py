#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Term based tool to view *colored*, *incremental* diff in a *Git/Mercurial/Svn*
workspace or from stdin, with *side by side* and *auto pager* support. Requires
python (>= 2.6.0) and ``less``.
"""

import difflib
import fcntl
import os
import re
import signal
import struct
import subprocess
import sys
import termios
import unicodedata

META_INFO = {
    'version'     : '1.3',
    'license'     : 'BSD-3',
    'author'      : 'Matt Wang',
    'url'         : 'https://github.com/ymattw/ydiff',
    'keywords'    : 'colored incremental side-by-side diff',
    'description' : ('View colored, incremental diff in a workspace or from '
                     'stdin, with side by side and auto pager support')
}

if sys.hexversion < 0x02060000:
    raise SystemExit('*** Requires python >= 2.6.0')    # pragma: no cover


try:
    unicode
except NameError:
    unicode = str


class Color(object):
    RESET = '\x1b[0m'
    UNDERLINE = '\x1b[4m'
    REVERSE = '\x1b[7m'
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    BLUE = '\x1b[34m'
    MAGENTA = '\x1b[35m'
    CYAN = '\x1b[36m'
    LIGHTRED = '\x1b[1;31m'
    LIGHTGREEN = '\x1b[1;32m'
    LIGHTYELLOW = '\x1b[1;33m'
    LIGHTBLUE = '\x1b[1;34m'
    LIGHTMAGENTA = '\x1b[1;35m'
    LIGHTCYAN = '\x1b[1;36m'


# Keys for revision control probe, diff and log (optional) with diff
VCS_INFO = {
    'Git': {
        'probe': ['git', 'rev-parse'],
        'diff': ['git', 'diff', '--no-ext-diff'],
        'log': ['git', 'log', '--patch'],
    },
    'Mercurial': {
        'probe': ['hg', 'summary'],
        'diff': ['hg', 'diff'],
        'log': ['hg', 'log', '--patch'],
    },
    'Perforce': {
        'probe': ['p4', 'dirs', '.'],
        'diff': ['p4', 'diff'],
        'log': None,
    },
    'Svn': {
        'probe': ['svn', 'info'],
        'diff': ['svn', 'diff'],
        'log': ['svn', 'log', '--diff', '--use-merge-history'],
    },
}


def revision_control_probe():
    """Returns version control name (key in VCS_INFO) or None."""
    for vcs_name, ops in VCS_INFO.items():
        if check_command_status(ops.get('probe')):
            return vcs_name


def revision_control_diff(vcs_name, args):
    """Return diff from revision control system."""
    cmd = VCS_INFO[vcs_name]['diff']
    return subprocess.Popen(cmd + args, stdout=subprocess.PIPE).stdout


def revision_control_log(vcs_name, args):
    """Return log from revision control system or None."""
    cmd = VCS_INFO[vcs_name].get('log')
    if cmd is not None:
        return subprocess.Popen(cmd + args, stdout=subprocess.PIPE).stdout


def colorize(text, start_color, end_color=Color.RESET):
    return start_color + text + end_color


def strsplit(text, width):
    r"""Splits a string into two substrings, respecting ANSI escape sequences.

    Returns a 3-tuple: (first substring, second substring, number of visible
    chars in the first substring).

    If some color was active at the splitting point, then the first string is
    appended with the resetting sequence, and the second string is prefixed
    with all active colors.
    """
    first = ''
    found_colors = ''
    chars_cnt = 0
    total_chars = len(text)
    i = 0

    while i < total_chars:
        if text[i] == '\x1b':
            color_end = text.find('m', i)
            if color_end != -1:
                color = text[i:color_end + 1]
                if color == Color.RESET:
                    found_colors = ''
                else:
                    found_colors += color

                first += color
                i = color_end + 1
                continue

        if chars_cnt >= width:
            break

        char = text[i]
        char_width = 2 if unicodedata.east_asian_width(char) in 'WF' else 1
        chars_cnt += char_width
        first += char
        i += 1

    first += Color.RESET if found_colors else ''
    second = found_colors + text[i:]
    return first, second, chars_cnt


def strtrim(text, width, wrap_char, pad):
    r"""strtrim() trims given string respecting the escape sequences (using
    strsplit), so that if text is larger than width, it's trimmed to have
    width-1 chars plus wrap_char. Additionally, if pad is True, short strings
    are padded with space to have exactly needed width.

    Returns resulting string.
    """
    text, _, tlen = strsplit(text, width + 1)
    if tlen > width:
        text, _, _ = strsplit(text, width - 1)
        text += wrap_char
    elif pad:
        # The string is short enough, but it might need to be padded.
        text = '%s%*s' % (text, width - tlen, '')
    return text


class Hunk(object):

    def __init__(self, hunk_headers, hunk_meta, old_addr, new_addr):
        self._hunk_headers = hunk_headers
        self._hunk_meta = hunk_meta
        self._old_addr = old_addr   # tuple (start, offset)
        self._new_addr = new_addr   # tuple (start, offset)
        self._hunk_list = []        # list of tuple (attr, line)

    def append(self, hunk_line):
        """hunk_line is a 2-element tuple: (attr, text), where attr is:
                '-': old, '+': new, ' ': common
        """
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
        return [line for (attr, line) in self._hunk_list if attr != '+']

    def _get_new_text(self):
        return [line for (attr, line) in self._hunk_list if attr != '-']

    def is_completed(self):
        old_completed = self._old_addr[1] == len(self._get_old_text())
        new_completed = self._new_addr[1] == len(self._get_new_text())
        return old_completed and new_completed


class UnifiedDiff(object):

    def __init__(self, headers, old_path, new_path, hunks):
        self._headers = headers
        self._old_path = old_path
        self._new_path = new_path
        self._hunks = hunks

    def is_old_path(self, line):
        return line.startswith('--- ')

    def is_new_path(self, line):
        return line.startswith('+++ ')

    def is_hunk_meta(self, line):
        """Minimal valid hunk meta is like '@@ -1 +1 @@', note extra chars
        might occur after the ending @@, e.g. in git log.  '## ' usually
        indicates svn property changes in output from `svn log --diff`
        """
        return (line.startswith('@@ -') and line.find(' @@') >= 8 or
                line.startswith('## -') and line.find(' ##') >= 8)

    def parse_hunk_meta(self, hunk_meta):
        # @@ -3,7 +3,6 @@
        a = hunk_meta.split()[1].split(',')   # -3 7
        if len(a) > 1:
            old_addr = (int(a[0][1:]), int(a[1]))
        else:
            # @@ -1 +1,2 @@
            old_addr = (int(a[0][1:]), 1)

        b = hunk_meta.split()[2].split(',')   # +3 6
        if len(b) > 1:
            new_addr = (int(b[0][1:]), int(b[1]))
        else:
            # @@ -0,0 +1 @@
            new_addr = (int(b[0][1:]), 1)

        return old_addr, new_addr

    def parse_hunk_line(self, line):
        return line[0], line[1:]

    def is_old(self, line):
        """Exclude old path and header line from svn log --diff output, allow
        '----' likely to see in diff from yaml file
        """
        return (line.startswith('-') and not self.is_old_path(line) and
                not re.match(r'^-{72}$', line.rstrip()))

    def is_new(self, line):
        return line.startswith('+') and not self.is_new_path(line)

    def is_common(self, line):
        return line.startswith(' ')

    def is_eof(self, line):
        # \ No newline at end of file
        # \ No newline at end of property
        return line.startswith(r'\ No newline at end of')

    def is_only_in_dir(self, line):
        return line.startswith('Only in ')

    def is_binary_differ(self, line):
        return re.match('^Binary files .* differ$', line.rstrip())


class DiffParser(object):

    def __init__(self, stream):
        self._stream = stream

    def parse(self):
        """parse all diff lines, construct a list of UnifiedDiff objects"""
        diff = UnifiedDiff([], None, None, [])
        headers = []

        for line in self._stream:
            line = decode(line)

            if diff.is_old_path(line):
                # This is a new diff when current hunk is not yet genreated or
                # is completed.  We yield previous diff if exists and construct
                # a new one for this case.  Otherwise it's acutally an 'old'
                # line starts with '--- '.
                if (not diff._hunks or diff._hunks[-1].is_completed()):
                    if diff._old_path and diff._new_path and diff._hunks:
                        yield diff
                    diff = UnifiedDiff(headers, line, None, [])
                    headers = []
                else:
                    diff._hunks[-1].append(diff.parse_hunk_line(line))

            elif diff.is_new_path(line) and diff._old_path:
                if not diff._new_path:
                    diff._new_path = line
                else:
                    diff._hunks[-1].append(diff.parse_hunk_line(line))

            elif diff.is_hunk_meta(line):
                hunk_meta = line
                try:
                    old_addr, new_addr = diff.parse_hunk_meta(hunk_meta)
                except (IndexError, ValueError):
                    raise RuntimeError('invalid hunk meta: %s' % hunk_meta)
                hunk = Hunk(headers, hunk_meta, old_addr, new_addr)
                headers = []
                diff._hunks.append(hunk)

            elif diff._hunks and not headers and (diff.is_old(line) or
                                                  diff.is_new(line) or
                                                  diff.is_common(line)):
                diff._hunks[-1].append(diff.parse_hunk_line(line))

            elif diff.is_eof(line):
                pass

            elif diff.is_only_in_dir(line) or diff.is_binary_differ(line):
                # 'Only in foo:' and 'Binary files ... differ' are considered
                # as separate diffs, so yield current diff, then this line
                if diff._old_path and diff._new_path and diff._hunks:
                    # Current diff is comppletely constructed
                    yield diff
                headers.append(line)
                yield UnifiedDiff(headers, '', '', [])
                headers = []
                diff = UnifiedDiff([], None, None, [])

            else:
                # Non-recognized lines: headers or hunk headers
                headers.append(line)

        # Validate and yield the last patch set if it is not yielded yet
        if diff._old_path:
            assert diff._new_path is not None
            if diff._hunks:
                assert len(diff._hunks[-1]._hunk_meta) > 0
                assert len(diff._hunks[-1]._hunk_list) > 0
            yield diff

        if headers:
            # Tolerate dangling headers, yield an object with header lines only
            yield UnifiedDiff(headers, '', '', [])


class DiffMarker(object):

    def __init__(self, side_by_side=False, width=0, tab_width=8, wrap=False):
        self._side_by_side = side_by_side
        self._width = width
        self._tab_width = tab_width
        self._wrap = wrap

        self._markup_header = lambda x: colorize(x, Color.CYAN)
        self._markup_old_path = lambda x: colorize(x, Color.YELLOW)
        self._markup_new_path = lambda x: colorize(x, Color.YELLOW)
        self._markup_hunk_header = lambda x: colorize(x, Color.LIGHTCYAN)
        self._markup_hunk_meta = lambda x: colorize(x, Color.LIGHTBLUE)
        self._markup_common = lambda x: colorize(x, Color.RESET)
        self._markup_old = lambda x: colorize(x, Color.LIGHTRED)
        self._markup_new = lambda x: colorize(x, Color.GREEN)

    def markup(self, diff):
        """Returns a generator"""
        if self._side_by_side:
            for line in self._markup_side_by_side(diff):
                yield line
        else:
            for line in self._markup_traditional(diff):
                yield line

    def _markup_traditional(self, diff):
        """Returns a generator"""
        for line in diff._headers:
            yield self._markup_header(line)

        yield self._markup_old_path(diff._old_path)
        yield self._markup_new_path(diff._new_path)

        for hunk in diff._hunks:
            for hunk_header in hunk._hunk_headers:
                yield self._markup_hunk_header(hunk_header)
            yield self._markup_hunk_meta(hunk._hunk_meta)
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
                        yield (self._markup_old('-') +
                               self._markup_mix(old[1], Color.RED))
                        yield (self._markup_new('+') +
                               self._markup_mix(new[1], Color.GREEN))
                else:
                    yield self._markup_common(' ' + old[1])

    def _markup_side_by_side(self, diff):
        """Returns a generator"""

        def _normalize(line):
            index = 0
            while True:
                index = line.find('\t', index)
                if (index == -1):
                    break
                # ignore special codes
                offset = (line.count('\x00', 0, index) * 2 +
                          line.count('\x01', 0, index))
                # next stop modulo tab width
                width = self._tab_width - (index - offset) % self._tab_width
                line = line[:index] + ' ' * width + line[(index + 1):]
            return line.replace('\n', '').replace('\r', '')

        def _fit_with_marker_mix(text, base_color):
            """Wrap input text which contains mdiff tags, markup at the
            meantime
            """
            out = [base_color]
            tag_re = re.compile(r'\x00[+^-]|\x01')

            while text:
                if text.startswith('\x00-'):    # del
                    out.append(Color.REVERSE + base_color)
                    text = text[2:]
                elif text.startswith('\x00+'):  # add
                    out.append(Color.REVERSE + base_color)
                    text = text[2:]
                elif text.startswith('\x00^'):  # change
                    out.append(Color.UNDERLINE + base_color)
                    text = text[2:]
                elif text.startswith('\x01'):   # reset
                    if len(text) > 1:
                        out.append(Color.RESET + base_color)
                    text = text[1:]
                else:
                    # FIXME: utf-8 wchar might break the rule here, e.g.
                    # u'\u554a' takes double width of a single letter, also
                    # this depends on your terminal font.
                    out.append(text[0])
                    text = text[1:]

            out.append(Color.RESET)
            return ''.join(out)

        # Set up number width, note last hunk might be empty
        try:
            (start, offset) = diff._hunks[-1]._old_addr
            max1 = start + offset - 1
            (start, offset) = diff._hunks[-1]._new_addr
            max2 = start + offset - 1
        except IndexError:
            max1 = max2 = 0
        num_width = max(len(str(max1)), len(str(max2)))

        # Set up line width
        width = self._width
        if width <= 0:
            # Autodetection of text width according to terminal size
            try:
                # Each line is like 'nnn TEXT nnn TEXT\n', so width is half of
                # [terminal size minus the line number columns and 3 separating
                # spaces
                width = (terminal_width() - num_width * 2 - 3) // 2
            except Exception:
                width = 80

        # Setup lineno and line format
        left_num_fmt = colorize('%%(left_num)%ds' % num_width, Color.YELLOW)
        right_num_fmt = colorize('%%(right_num)%ds' % num_width, Color.YELLOW)
        line_fmt = (left_num_fmt + ' %(left)s ' + Color.RESET +
                    right_num_fmt + ' %(right)s\n')

        # yield header, old path and new path
        for line in diff._headers:
            yield self._markup_header(line)
        yield self._markup_old_path(diff._old_path)
        yield self._markup_new_path(diff._new_path)

        # yield hunks
        for hunk in diff._hunks:
            for hunk_header in hunk._hunk_headers:
                yield self._markup_hunk_header(hunk_header)
            yield self._markup_hunk_meta(hunk._hunk_meta)
            for old, new, changed in hunk.mdiff():
                if old[0]:
                    left_num = str(hunk._old_addr[0] + int(old[0]) - 1)
                else:
                    left_num = ' '

                if new[0]:
                    right_num = str(hunk._new_addr[0] + int(new[0]) - 1)
                else:
                    right_num = ' '

                left = _normalize(old[1])
                right = _normalize(new[1])

                if changed:
                    if not old[0]:
                        left = ''
                        right = right.rstrip('\x01')
                        if right.startswith('\x00+'):
                            right = right[2:]
                        right = self._markup_new(right)
                    elif not new[0]:
                        left = left.rstrip('\x01')
                        if left.startswith('\x00-'):
                            left = left[2:]
                        left = self._markup_old(left)
                        right = ''
                    else:
                        left = _fit_with_marker_mix(left, Color.RED)
                        right = _fit_with_marker_mix(right, Color.GREEN)
                else:
                    left = self._markup_common(left)
                    right = self._markup_common(right)

                if self._wrap:
                    # Need to wrap long lines, so here we'll iterate,
                    # shaving off `width` chars from both left and right
                    # strings, until both are empty. Also, line number needs to
                    # be printed only for the first part.
                    lncur = left_num
                    rncur = right_num
                    while left or right:
                        # Split both left and right lines, preserving escaping
                        # sequences correctly.
                        lcur, left, llen = strsplit(left, width)
                        rcur, right, rlen = strsplit(right, width)

                        # Pad left line with spaces if needed
                        if llen < width:
                            lcur = '%s%*s' % (lcur, width - llen, '')

                        yield line_fmt % {
                            'left_num': lncur,
                            'left': lcur,
                            'right_num': rncur,
                            'right': rcur
                        }

                        # Clean line numbers for further iterations
                        lncur = ''
                        rncur = ''
                else:
                    # Don't need to wrap long lines; instead, a trailing '>'
                    # char needs to be appended.
                    wrap_char = colorize('>', Color.LIGHTMAGENTA)
                    left = strtrim(left, width, wrap_char, len(right) > 0)
                    right = strtrim(right, width, wrap_char, False)

                    yield line_fmt % {
                        'left_num': left_num,
                        'left': left,
                        'right_num': right_num,
                        'right': right
                    }

    def _markup_mix(self, line, base_color):
        del_code = Color.REVERSE + base_color
        add_code = Color.REVERSE + base_color
        chg_code = Color.UNDERLINE + base_color
        rst_code = Color.RESET + base_color
        line = line.replace('\x00-', del_code)
        line = line.replace('\x00+', add_code)
        line = line.replace('\x00^', chg_code)
        line = line.replace('\x01', rst_code)
        return colorize(line, base_color)


def markup_to_pager(stream, opts):
    """Pipe unified diff stream to pager (less)."""
    pager_cmd = [opts.pager]
    pager_opts = opts.pager_options.split(' ') if opts.pager_options else []

    if opts.pager is None:
        pager_cmd = ['less']
        if not os.getenv('LESS') and not opts.pager_options:
            # Args stolen from github.com/git/git/blob/master/pager.c
            pager_opts = ['-FRSX', '--shift 1']

    pager_cmd.extend(pager_opts)
    pager = subprocess.Popen(
        pager_cmd, stdin=subprocess.PIPE, stdout=sys.stdout)

    diffs = DiffParser(stream).parse()
    for diff in diffs:
        marker = DiffMarker(side_by_side=opts.side_by_side, width=opts.width,
                            tab_width=opts.tab_width, wrap=opts.wrap)
        color_diff = marker.markup(diff)
        for line in color_diff:
            pager.stdin.write(line.encode('utf-8'))

    pager.stdin.close()
    pager.wait()


def check_command_status(arguments):
    """Return True if command returns 0."""
    try:
        return subprocess.call(
            arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
    except OSError:
        return False


def decode(line):
    """Decode UTF-8 if necessary."""
    if isinstance(line, unicode):
        return line

    for encoding in ['utf-8', 'latin1']:
        try:
            return line.decode(encoding)
        except UnicodeDecodeError:
            pass

    return '*** ydiff: undecodable bytes ***\n'


def terminal_width():
    """Returns terminal width. Taken from https://gist.github.com/marsam/7268750
    but removed win32 support which depends on 3rd party extension. Will raise
    IOError or AttributeError when impossible to detect.
    """
    s = struct.pack('HHHH', 0, 0, 0, 0)
    x = fcntl.ioctl(1, termios.TIOCGWINSZ, s)
    _, width = struct.unpack('HHHH', x)[0:2]  # height unused
    return width


def trap_interrupts(entry_fn):
    def entry_wrapper():
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if sys.platform != 'win32':
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            return entry_fn()
        else:
            import errno
            try:
                return entry_fn()
            except IOError as e:
                if e.errno not in [errno.EPIPE, errno.EINVAL]:
                    raise
                return 0
    return entry_wrapper


@trap_interrupts
def main():
    from optparse import (OptionParser, BadOptionError, AmbiguousOptionError,
                          OptionGroup)

    class PassThroughOptionParser(OptionParser):
        """Stop parsing on first unknown option (e.g. --cached, -U10) and pass
        them down.  Note the `opt_str` in exception object does not give us
        chance to take the full option back, e.g. for '-U10' it will only
        contain '-U' and the '10' part will be lost.  Ref: http://goo.gl/IqY4A
        (on stackoverflow).  My hack is to try parse and insert a '--' in place
        and parse again.  Let me know if someone has better solution.
        """
        def _process_args(self, largs, rargs, values):
            left = largs[:]
            right = rargs[:]
            try:
                OptionParser._process_args(self, left, right, values)
            except (BadOptionError, AmbiguousOptionError):
                parsed_num = len(rargs) - len(right) - 1
                rargs.insert(parsed_num, '--')
            OptionParser._process_args(self, largs, rargs, values)

    usage = """%prog [options] [file|dir ...]"""
    parser = PassThroughOptionParser(
        usage=usage, description=META_INFO['description'],
        version='%%prog %s' % META_INFO['version'])
    parser.add_option(
        '-s', '--side-by-side', action='store_true',
        help='enable side-by-side mode')
    parser.add_option(
        '-w', '--width', type='int', default=80, metavar='N',
        help='set text width for side-by-side mode, 0 for auto detection, '
             'default is 80')
    parser.add_option(
        '-l', '--log', action='store_true',
        help='show log with changes from revision control')
    parser.add_option(
        '-c', '--color', default='auto', metavar='M',
        help="""colorize mode 'auto' (default), 'always', or 'never'""")
    parser.add_option(
        '-t', '--tab-width', type='int', default=8, metavar='N',
        help="""convert tab characters to this many spaces (default: 8)""")
    parser.add_option(
        '', '--wrap', action='store_true',
        help='wrap long lines in side-by-side view')
    parser.add_option(
        '-p', '--pager', metavar='M',
        help="""pager application, suggested values are 'less' """
             """or 'cat'""")
    parser.add_option(
        '-o', '--pager-options', metavar='M',
        help="""options to supply to pager application""")

    # Hack: use OptionGroup text for extra help message after option list
    option_group = OptionGroup(
        parser, 'Note', ('Option parser will stop on first unknown option '
                         'and pass them down to underneath revision control. '
                         'Environment variable YDIFF_OPTIONS may be used to '
                         'specify default options that will be placed at the '
                         'beginning of the argument list.'))
    parser.add_option_group(option_group)

    # Place possible options defined in YDIFF_OPTIONS at the beginning of argv
    ydiff_opts = [x for x in os.getenv('YDIFF_OPTIONS', '').split(' ') if x]
    opts, args = parser.parse_args(ydiff_opts + sys.argv[1:])

    stream = None
    if not sys.stdin.isatty():
        stream = getattr(sys.stdin, 'buffer', sys.stdin)
    else:
        vcs = revision_control_probe()
        if vcs is None:
            supported_vcs = ', '.join(sorted(VCS_INFO.keys()))
            sys.stderr.write('*** Not in a supported workspace, supported are:'
                             ' %s\n' % supported_vcs)
            return 1

        if opts.log:
            stream = revision_control_log(vcs, args)
            if stream is None:
                sys.stderr.write('*** %s has no log support.\n' % vcs)
                return 1
        else:
            # 'diff' is a must have feature.
            stream = revision_control_diff(vcs, args)

    if (opts.color == 'always' or
            (opts.color == 'auto' and sys.stdout.isatty())):
        markup_to_pager(stream, opts)
    else:
        # pipe out stream untouched to make sure it is still a patch
        byte_output = getattr(sys.stdout, 'buffer', sys.stdout)
        for line in stream:
            byte_output.write(line)

    if stream is not None:
        stream.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())

# vim:set et sts=4 sw=4 tw=79:
