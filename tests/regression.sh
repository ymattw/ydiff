#!/bin/bash

set -o errexit

SELF_DIR=$(cd $(dirname $0) && pwd) || exit 1
CDIFF=$SELF_DIR/../cdiff

function pass()
{
    if [[ -t 1 ]]; then
        echo -e "\x1b[01;32mPASS\x1b[0m" "$*"
    else
        echo "PASS" "$*"
    fi
}

function fail()
{
    if [[ -t 1 ]]; then
        echo -e "\x1b[01;31mFAIL\x1b[0m" "$*"
    else
        echo "FAIL" "$*"
    fi
}

function cmpOutput()
{
    local input=${1:?}
    local expected_out=${2:?}
    local cdiff_opt=${3:-""}

    echo -n "Test option '$cdiff_opt' with input '$input' ... "
    if $CDIFF $cdiff_opt $input | diff -ubq $expected_out - >& /dev/null; then
        pass
        return 0
    else
        fail "(expected output: '$expected_out')"
        return 1
    fi
}

function main()
{
    local rc=0
    local d

    for d in $SELF_DIR/*/; do
        cmpOutput "${d}in.diff" ${d}out.normal "-c always" || rc=1
        cmpOutput "${d}in.diff" ${d}out.side-by-side "-c always -s" || rc=1
        cmpOutput "${d}in.diff" ${d}out.w70 "-c always -s -w70" || rc=1
        cmpOutput "${d}in.diff" "${d}in.diff" "-c auto" || rc=1
        cmpOutput "${d}in.diff" "${d}in.diff" "-c auto -s" || rc=1
        cmpOutput "${d}in.diff" "${d}in.diff" "-c auto -s -w70" || rc=1
    done
    return $rc
}

main "$@"

# vim:set et sts=4 sw=4:
