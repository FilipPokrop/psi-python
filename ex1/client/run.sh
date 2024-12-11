#!/bin/sh

[ -n "$CMD" ] || CMD="python main.py"

/scripts/run_tcpdump.sh client

${CMD} 
STATUS=$?

sleep 0.3

exit $STATUS
