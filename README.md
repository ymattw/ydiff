## About

View **incremental**, **colored** diff in unified format or in **side by side**
mode with **auto pager**.  Requires python (>= 2.5.0) and `less`.

![Default](http://ymattw.github.com/cdiff/img/default.png)
![Side by side](http://ymattw.github.com/cdiff/img/side-by-side.png)

## Installation

Save [src/cdiff.py](https://raw.github.com/ymattw/cdiff/master/src/cdiff.py) to
whatever directory which is in your `$PATH`, for example, `$HOME/bin` is in my
`$PATH`, so I save the script there and name as `cdiff`.

    curl -ksS https://raw.github.com/ymattw/cdiff/master/src/cdiff.py > ~/bin/cdiff
    chmod +x ~/bin/cdiff
    
## Usage
    
Just give it a diff (patch) file or pipe a diff to it.  Use option `-s` for
side-by-side view, and option `-w N` to set a text width other than default
`80`.  See examples below

View a diff (patch) file:

    cdiff foo.patch             # view incremental, colored udiff
    cdiff foo.patch -s          # view in side by side mode
    cdiff foo.patch -s -w 90    # use text width 90 other than default 80
    
Read diff from svn:

    svn diff | cdiff
    svn diff | cdiff -s
    svn diff | cdiff -s -w 90
    
Read diff from git:

    git diff | cdiff -s
    git log -p -2 | cdiff -s
    git show <commit> | cdiff -s

Redirect output to another patch file is safe:

    svn diff | cdiff -s > my.patch

## Known issue

- Only support unified format for input diff
- Side by side mode has alignment problem for wide chars
