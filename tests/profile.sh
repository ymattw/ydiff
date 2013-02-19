#!/bin/bash

OUTPUT=${1:?"output file required"}

SELF_DIR=$(cd $(dirname $0) && pwd) || exit 1
CDIFF_PY=$SELF_DIR/../cdiff.py

# To test with py3k: PYTHON=python3 make test
PYTHON=${PYTHON:-python}

set -o errexit
STATS="stats.$$.tmp"

for i in {1..100}; do cat "tests/svn/in.diff"; done \
    | $PYTHON -m cProfile -o $STATS $CDIFF_PY -c always -s -w 60 \
    > /dev/null

$PYTHON -c "import pstats;  p = pstats.Stats('$STATS'); \
    p.strip_dirs().sort_stats('time').print_stats('cdiff')" \
    | tee $OUTPUT

rm -f $STATS

# vim:set et sts=4 sw=4:
