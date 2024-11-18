#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Terminmal based tool to view colored, incremental diffs in a version-controlled
workspace or from stdin, in side-by-side or unified mode, and auto paged.
"""

import difflib
import os
import re
import shutil
import signal
import subprocess
import sys
import unicodedata

PKG_INFO = {
    'version'     : '1.4.2',
    'license'     : 'BSD-3',
    'author'      : 'Matt Wang',
    'url'         : 'https://github.com/ymattw/ydiff',
    'keywords'    : 'colored incremental side-by-side diff',
    'description' : ('View colored, incremental diff in a workspace or from '
                     'stdin, in side-by-side or unified moded, and auto paged')
}

if sys.hexversion < 0x03030000:
    raise SystemExit('*** Requires python >= 3.3.0')    # pragma: no cover


class _Color:
    RESET = '\x1b[0m'
    REVERSE = '\x1b[7m'
    # https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit
    FG_RED = '\x1b[31m'
    FG_GREEN = '\x1b[32m'
    FG_YELLOW = '\x1b[33m'
    FG_BLUE = '\x1b[34m'
    FG_CYAN = '\x1b[36m'
    FG_BRIGHT_MAGENTA = '\x1b[95m'
    FG_BRIGHT_CYAN = '\x1b[96m'
    # https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit
    FG8_GRAY = '\x1b[38;5;235m'
    BG8_DARK_RED = '\x1b[48;5;52m'
    BG8_RED = '\x1b[48;5;88m'
    BG8_DARK_GREEN = '\x1b[48;5;22m'
    BG8_GREEN = '\x1b[48;5;28m'
    BG8_LIGHT_RED = '\x1b[48;5;217m'
    BG8_DIMMED_RED = '\x1b[48;5;210m'
    BG8_LIGHT_GREEN = '\x1b[48;5;194m'
    BG8_DIMMED_GREEN = '\x1b[48;5;157m'


_THEMES = {
    'default': {
        # kind: [effect...]
        'header': [_Color.FG_CYAN],
        'old_path': [_Color.FG_YELLOW],
        'new_path': [_Color.FG_YELLOW],
        'hunk_header': [_Color.FG_CYAN],
        'hunk_meta': [_Color.FG_BLUE],
        'common_line': [_Color.RESET],
        'old_line': [_Color.FG_RED],
        'new_line': [_Color.FG_GREEN],
        'deleted_text': [_Color.REVERSE, _Color.FG_RED],
        'inserted_text': [_Color.REVERSE, _Color.FG_GREEN],
        'replaced_old_text': [_Color.REVERSE, _Color.FG_RED],
        'replaced_new_text': [_Color.REVERSE, _Color.FG_GREEN],
        'old_line_number': [_Color.FG_YELLOW],
        'new_line_number': [_Color.FG_YELLOW],
        'file_separator': [_Color.FG_BRIGHT_CYAN],
        'wrap_marker': [_Color.FG_BRIGHT_MAGENTA],
    },
    'dark': {
        # kind: [effect...]
        'header': [_Color.FG_CYAN],
        'old_path': [_Color.BG8_DARK_RED],
        'new_path': [_Color.BG8_DARK_GREEN],
        'hunk_header': [_Color.FG_CYAN],
        'hunk_meta': [_Color.FG_BLUE],
        'common_line': [_Color.RESET],
        'old_line': [_Color.BG8_DARK_RED],
        'new_line': [_Color.BG8_DARK_GREEN],
        'deleted_text': [_Color.BG8_RED],
        'inserted_text': [_Color.FG8_GRAY, _Color.BG8_GREEN],
        'replaced_old_text': [_Color.BG8_RED],
        'replaced_new_text': [_Color.FG8_GRAY, _Color.BG8_GREEN],
        'old_line_number': [_Color.FG_YELLOW],
        'new_line_number': [_Color.FG_YELLOW],
        'file_separator': [_Color.FG_BRIGHT_CYAN],
        'wrap_marker': [_Color.FG_BRIGHT_MAGENTA],
    },
    'light': {
        # kind: [effect...]
        'header': [_Color.FG_CYAN],
        'old_path': [_Color.BG8_LIGHT_RED],
        'new_path': [_Color.BG8_LIGHT_GREEN],
        'hunk_header': [_Color.FG_CYAN],
        'hunk_meta': [_Color.FG_BLUE],
        'common_line': [_Color.RESET],
        'old_line': [_Color.BG8_LIGHT_RED],
        'new_line': [_Color.BG8_LIGHT_GREEN],
        'deleted_text': [_Color.BG8_DIMMED_RED],
        'inserted_text': [_Color.FG8_GRAY, _Color.BG8_DIMMED_GREEN],
        'replaced_old_text': [_Color.BG8_DIMMED_RED],
        'replaced_new_text': [_Color.FG8_GRAY, _Color.BG8_DIMMED_GREEN],
        'old_line_number': [_Color.FG_YELLOW],
        'new_line_number': [_Color.FG_YELLOW],
        'file_separator': [_Color.FG_BRIGHT_CYAN],
        'wrap_marker': [_Color.FG_BRIGHT_MAGENTA],
    },
}


def _colorize(text, kind, theme='default'):
    if kind == 'replaced_old_text':
        base_color = ''.join(_THEMES[theme]['old_line'])
        del_color = ''.join(_THEMES[theme]['replaced_old_text'])
        chg_color = ''.join(_THEMES[theme]['deleted_text'])
        rst_color = _Color.RESET + base_color
        text = text.replace('\0-', del_color)
        text = text.replace('\0^', chg_color)
        text = text.replace('\1', rst_color)
    elif kind == 'replaced_new_text':
        base_color = ''.join(_THEMES[theme]['new_line'])
        add_color = ''.join(_THEMES[theme]['replaced_new_text'])
        chg_color = ''.join(_THEMES[theme]['inserted_text'])
        rst_color = _Color.RESET + base_color
        text = text.replace('\0+', add_color)
        text = text.replace('\0^', chg_color)
        text = text.replace('\1', rst_color)
    else:
        base_color = ''.join(_THEMES[theme][kind])
    return base_color + text + _Color.RESET


def _strsplit(text, width, color_codes):
    r"""Splits a string into two substrings, respecting involved color codes.

    Returns a 3-tuple: (left substring, right substring, width of visible
    chars in the left substring).

    If some color was active at the splitting point, then the left string is
    appended with the resetting sequence, and the second string is prefixed
    with all active colors.
    """
    left = ''
    seen_colors = ''
    left_width = 0
    total_chars = len(text)
    i = 0

    while i < total_chars:
        if text[i] == '\x1b':
            for c in color_codes:
                if text.startswith(c, i):
                    seen_colors = '' if c == _Color.RESET else seen_colors + c
                    left += c
                    i += len(c)
                    break
            else:  # not found
                left += text[i]
                i += 1
            continue

        if left_width >= width:
            break
        left += text[i]
        left_width += 1 + int(unicodedata.east_asian_width(text[i]) in 'WF')
        i += 1

    left += _Color.RESET if seen_colors else ''
    right = seen_colors + text[i:]
    return left, right, left_width


def _strtrim(text, width, wrap_char, pad, color_codes):
    r"""Trims given string respecting the involved color codes (using
    strsplit), so that if text is larger than width, it's trimmed to have
    width-1 chars plus wrap_char. Additionally, if pad is True, short strings
    are padded with space to have exactly needed width.

    Returns resulting string.
    """
    left, right, left_width = _strsplit(text, width, color_codes)
    if right or left_width > width:  # asian chars can cause exceeds
        left, _, _ = _strsplit(left, width - 1, color_codes)
        left += wrap_char
    elif pad:
        left = '%s%*s' % (left, width - left_width, '')
    return left


def _split_to_words(s: str) -> list:
    r"""Split to list of "words" for fine-grained comparison by breaking
    all uppercased/lowercased, camel and snake cased names at the "word"
    boundary. Note '\s' has to be here to match '\n'.
    """
    r = re.compile(r'[A-Z]{2,}|[A-Z][a-z]+|[a-z]{2,}|[A-Za-z0-9]+|\s|.')
    return r.findall(s)


def _word_diff(a: str, b: str) -> tuple:
    r"""Takes the from/to texts yield by Hunk.mdiff() which are part of the
    'changed' block, remove the special markers (\0-, \0+, \0^, \1), compare
    word by word and return two new texts with the markers reassemabled.

    Context: difflib._mdiff() is good for indention detection, but produces
    coarse-grained diffs for the 'changed' block when the similarity is below
    a certain ratio (hardcode 0.75). One example: "import foo" vs "import bar"
    is treated full line change instead of only "foo" changed to "bar".
    """
    for token in ['\0-', '\0+', '\0^', '\1']:
        a = a.replace(token, '')
        b = b.replace(token, '')

    old = _split_to_words(a)
    new = _split_to_words(b)
    xs = []
    ys = []
    for tag, i, j, m, n in difflib.SequenceMatcher(a=old, b=new).get_opcodes():
        x = ''.join(old[i:j])
        y = ''.join(new[m:n])
        # print('%s\t%s\n\t%s' % (tag, repr(x), repr(y)), file=sys.stderr)
        if tag == 'equal':
            xs.append(x)
            ys.append(y)
        elif tag == 'delete':
            xs.append('\0-%s\1' % x)
        elif tag == 'insert':
            ys.append('\0+%s\1' % y)
        elif tag == 'replace':
            xs.append('\0^%s\1' % x)
            ys.append('\0^%s\1' % y)
    return ''.join(xs), ''.join(ys)


class Hunk:

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


class UnifiedDiff:

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


class DiffParser:

    def __init__(self, stream):
        self._stream = stream  # bytes

    def parse(self):
        """parse all diff lines, construct a list of UnifiedDiff objects"""
        diff = UnifiedDiff([], None, None, [])
        headers = []

        for octets in self._stream:
            line = _decode(octets)

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


class DiffMarker:

    def __init__(self, side_by_side=False, width=0, tab_width=8, wrap=False,
                 theme='default'):
        self._side_by_side = side_by_side
        self._width = width
        self._tab_width = tab_width
        self._wrap = wrap
        self._theme = theme
        self._codes = set(sum(_THEMES[theme].values(), []))

    def markup(self, diff):
        """Returns a generator"""
        if self._side_by_side:
            it = self._markup_side_by_side
        else:
            it = self._markup_unified
        for line in it(diff):
            yield line

    def _markup_unified(self, diff):
        """Returns a generator"""
        for line in diff._headers:
            yield _colorize(line, 'header', theme=self._theme)

        yield _colorize(diff._old_path, 'old_path', theme=self._theme)
        yield _colorize(diff._new_path, 'new_path', theme=self._theme)

        for hunk in diff._hunks:
            for hunk_header in hunk._hunk_headers:
                yield _colorize(hunk_header, 'hunk_header', theme=self._theme)
            yield _colorize(hunk._hunk_meta, 'hunk_meta', theme=self._theme)
            for old, new, changed in hunk.mdiff():
                if changed:
                    if not old[0]:
                        # The '+' char after \0 is kept
                        # DEBUG: yield 'NEW: %s %s\n' % (old, new)
                        line = new[1].strip('\0\1')
                        yield _colorize(line, 'new_line', theme=self._theme)
                    elif not new[0]:
                        # The '-' char after \0 is kept
                        # DEBUG: yield 'OLD: %s %s\n' % (old, new)
                        line = old[1].strip('\0\1')
                        yield _colorize(line, 'old_line', theme=self._theme)
                    else:
                        # DEBUG: yield 'CHG: %s %s\n' % (old, new)
                        a, b = _word_diff(old[1], new[1])
                        yield (_colorize('-', 'old_line', theme=self._theme) +
                               _colorize(a, 'replaced_old_text',
                                         theme=self._theme))
                        yield (_colorize('+', 'new_line', theme=self._theme) +
                               _colorize(b, 'replaced_new_text',
                                         theme=self._theme))
                else:
                    yield _colorize(' ' + old[1], 'common_line',
                                    theme=self._theme)

    def _markup_side_by_side(self, diff):
        """Returns a generator"""

        def _normalize(line):
            index = 0
            while True:
                index = line.find('\t', index)
                if index == -1:
                    break
                # ignore special codes
                offset = (line.count('\0', 0, index) * 2 +
                          line.count('\1', 0, index))
                # next stop modulo tab width
                width = self._tab_width - (index - offset) % self._tab_width
                line = line[:index] + ' ' * width + line[(index + 1):]
            return line.replace('\n', '').replace('\r', '')

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
            # Autodetection of text width according to terminal size.  Each
            # line is like 'nnn TEXT nnn TEXT\n', so width is half of terminal
            # size minus the line number columns and 3 separating spaces
            width = (_terminal_width() - num_width * 2 - 3) // 2

        # Setup lineno and line format
        num_fmt1 = _colorize('%%(left_num)%ds' % num_width, 'old_line_number',
                             theme=self._theme)
        num_fmt2 = _colorize('%%(right_num)%ds' % num_width, 'new_line_number',
                             theme=self._theme)
        line_fmt = (num_fmt1 + ' %(left)s ' + _Color.RESET +
                    num_fmt2 + ' %(right)s\n')

        # yield header, old path and new path
        for line in diff._headers:
            yield _colorize(line, 'header', theme=self._theme)
        yield _colorize(diff._old_path, 'old_path', theme=self._theme)
        yield _colorize(diff._new_path, 'new_path', theme=self._theme)

        # yield hunks
        for hunk in diff._hunks:
            for hunk_header in hunk._hunk_headers:
                yield _colorize(hunk_header, 'hunk_header', theme=self._theme)
            yield _colorize(hunk._hunk_meta, 'hunk_meta', theme=self._theme)
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
                        right = right.rstrip('\1')
                        if right.startswith('\0+'):
                            right = right[2:]
                        right = _colorize(right, 'new_line', theme=self._theme)
                    elif not new[0]:
                        left = left.rstrip('\1')
                        if left.startswith('\0-'):
                            left = left[2:]
                        left = _colorize(left, 'old_line', theme=self._theme)
                        right = ''
                    else:
                        left, right = _word_diff(left, right)
                        left = _colorize(left, 'replaced_old_text',
                                         theme=self._theme)
                        right = _colorize(right, 'replaced_new_text',
                                          theme=self._theme)
                else:
                    left = _colorize(left, 'common_line', theme=self._theme)
                    right = _colorize(right, 'common_line', theme=self._theme)

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
                        lcur, left, llen = _strsplit(left, width, self._codes)
                        rcur, right, _ = _strsplit(right, width, self._codes)

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
                    wrap_marker = _colorize('>', 'wrap_marker',
                                            theme=self._theme)
                    left = _strtrim(left, width, wrap_marker, len(right) > 0,
                                    self._codes)
                    right = _strtrim(right, width, wrap_marker, False,
                                     self._codes)

                    yield line_fmt % {
                        'left_num': left_num,
                        'left': left,
                        'right_num': right_num,
                        'right': right
                    }


def markup_to_pager(stream, opts):
    """Pipe unified diff stream (in bytes) to pager (less)."""
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

    marker = DiffMarker(side_by_side=opts.side_by_side, width=opts.width,
                        tab_width=opts.tab_width, wrap=opts.wrap,
                        theme=opts.theme)
    term_width = _terminal_width()
    diffs = DiffParser(stream).parse()
    # Fetch one diff first, output a separation line for the rest, if any.
    try:
        diff = next(diffs)
        for line in marker.markup(diff):
            pager.stdin.write(line.encode('utf-8'))
    except StopIteration:
        pass
    for diff in diffs:
        separator = _colorize('─' * (term_width - 1) + '\n', 'file_separator',
                              theme=opts.theme)
        pager.stdin.write(separator.encode('utf-8'))
        for line in marker.markup(diff):
            pager.stdin.write(line.encode('utf-8'))

    pager.stdin.close()
    pager.wait()


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
        'probe': ['p4', 'info'],
        'diff': ['p4', 'diff', '-du'],
        'log': None,
    },
    'Svn': {
        'probe': ['svn', 'info'],
        'diff': ['svn', 'diff'],
        'log': ['svn', 'log', '--diff', '--use-merge-history'],
    },
}


def _revision_control_probe():
    """Returns version control name (key in VCS_INFO) or None."""
    for vcs_name, ops in VCS_INFO.items():
        if _check_command_status(ops.get('probe')):
            return vcs_name


def _revision_control_diff(vcs_name, args):
    """Return diff from revision control system."""
    cmd = VCS_INFO[vcs_name]['diff']
    return subprocess.Popen(cmd + args, stdout=subprocess.PIPE).stdout


def _revision_control_log(vcs_name, args):
    """Return log from revision control system or None."""
    cmd = VCS_INFO[vcs_name].get('log')
    if cmd is not None:
        return subprocess.Popen(cmd + args, stdout=subprocess.PIPE).stdout


def _check_command_status(cmd: list) -> bool:
    """Return True if command returns 0."""
    try:
        return subprocess.call(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
    except OSError:
        return False


def _decode(octets):
    """Decode bytes (read from file)."""
    for encoding in ['utf-8', 'latin1']:
        try:
            return octets.decode(encoding)
        except UnicodeDecodeError:
            pass
    return '*** ydiff: undecodable bytes ***\n'


def _terminal_width():
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def _trap_interrupts(entry_fn):
    def _entry_wrapper():
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if sys.platform != 'win32':
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            return entry_fn()

        import errno
        try:
            return entry_fn()
        except IOError as e:
            if e.errno not in [errno.EPIPE, errno.EINVAL]:
                raise
            return 0
    return _entry_wrapper


@_trap_interrupts
def _main():
    from optparse import (OptionParser, BadOptionError, AmbiguousOptionError,
                          OptionGroup)

    class _PassThroughOptionParser(OptionParser):
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
    parser = _PassThroughOptionParser(
        usage=usage, description=PKG_INFO['description'],
        version='%%prog %s' % PKG_INFO['version'])
    parser.add_option(
        '-s', '--side-by-side', action='store_true', default=True,
        help='enable side-by-side mode (default True; DEPRECATED)')
    parser.add_option(
        '-u', '--unified', action='store_false', dest='side_by_side',
        help='show diff in unified mode (disables side-by-side mode)')
    parser.add_option(
        '-w', '--width', type='int', default=0, metavar='N',
        help='set text width for side-by-side mode, 0 (default) for auto '
             'detection and fallback to 80 when not possible')
    parser.add_option(
        '-l', '--log', action='store_true',
        help='show log with changes from revision control')
    parser.add_option(
        '-c', '--color', default='auto', metavar='WHEN',
        help="""colorize mode 'auto' (default), 'always', or 'never'""")
    parser.add_option(
        '-t', '--tab-width', type='int', default=8, metavar='N',
        help="""convert tab chars to this many spaces (default: 8)""")
    parser.add_option(
        '', '--wrap', action='store_true', default=True,
        help='wrap long lines in side-by-side mode (default True; DEPRECATED)')
    parser.add_option(
        '--nowrap', '--no-wrap', action='store_false', dest='wrap',
        help='do not wrap long lines in side-by-side mode')
    parser.add_option(
        '-p', '--pager', metavar='PAGER',
        help="""pager application to feed output to, default is 'less'""")
    parser.add_option(
        '-o', '--pager-options', metavar='OPT',
        help="""options to supply to pager application""")
    themes = ', '.join(['default'] + sorted(_THEMES.keys() - {'default'}))
    parser.add_option(
        '', '--theme', metavar='THEME', default='default',
        help="""option to pick a color theme (one of %s)""" % themes)

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
    if opts.theme not in _THEMES:
        sys.stderr.write('*** Unknown theme, supported are: %s\n' % themes)
        return 1

    stream = None
    if not sys.stdin.isatty():
        stream = getattr(sys.stdin, 'buffer', sys.stdin)
    else:
        vcs = _revision_control_probe()
        if vcs is None:
            supported_vcs = ', '.join(sorted(VCS_INFO.keys()))
            sys.stderr.write('*** Not in a supported workspace, supported are:'
                             ' %s\n' % supported_vcs)
            return 1

        if opts.log:
            stream = _revision_control_log(vcs, args)
            if stream is None:
                sys.stderr.write('*** %s has no log support.\n' % vcs)
                return 1
        else:
            # 'diff' is a must have feature.
            stream = _revision_control_diff(vcs, args)

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
    sys.exit(_main())

# vim:set et sts=4 sw=4 tw=79:
