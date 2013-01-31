## About

Diff viewer, side-by-side, auto pager with `less`.

## Install

Just download the `src/cdiff.py` and save to whatever directory which in your
`$PATH`, for example, `$HOME/bin` is in my `$PATH`, so I save the script there
and name as `cdiff`.

    curl -ksS https://raw.github.com/ymattw/cdiff/master/src/cdiff.py > ~/bin/cdiff
    
## Usage
    
Read diff from svn, use option `-s` for side-by-side view, use option `-w` to
use text width other than default `80`.  You don't need `less`, it's automatic:

    svn diff | cdiff
    svn diff | cdiff -s
    svn diff | cdiff -s -w 90
    
Read diff from git:

    git diff | cdiff -s
    git log -p -2 | cdiff -s
    git show <commit> | cdiff -s

View a diff (patch) file:

    cdiff foo.patch
    cdiff foo.patch -s
    cdiff foo.patch -s -w 90

Redirect output to another patch file is safe:

    svn diff | cdiff -s > my.patch
