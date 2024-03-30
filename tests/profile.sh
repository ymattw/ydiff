#!/bin/bash

if (( $# < 1 )); then
    echo "Usage: $0 <input diff files...>"
    exit 1
fi

SELF_DIR=$(cd $(dirname $0) && pwd) || exit 1
YDIFF_PY=$SELF_DIR/../ydiff.py

PYTHON=${PYTHON:-python3}
unset YDIFF_OPTIONS

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
