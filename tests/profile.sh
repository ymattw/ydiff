#!/bin/bash

if (( $# < 1 )); then
    echo "Usage: $d <input diff files...>"
    exit 1
fi

SELF_DIR=$(cd $(dirname $0) && pwd) || exit 1
YDIFF_PY=$SELF_DIR/../ydiff.py

# To test with py3k: PYTHON=python3 make test
PYTHON=${PYTHON:-python}
unset YDIFF_OPTIONS
unset CDIFF_OPTIONS

set -o errexit

STATS="stats.$$.tmp"
OUTPUT="profile.$$.tmp"

cat "$@" \
    | $PYTHON -m cProfile -o $STATS $YDIFF_PY -c always -s -w 60 \
    > /dev/null

$PYTHON -c "import pstats;  p = pstats.Stats('$STATS'); \
    p.strip_dirs().sort_stats('time').print_stats('ydiff|difflib')" \
    | tee $OUTPUT

rm -f $STATS

# vim:set et sts=4 sw=4:
