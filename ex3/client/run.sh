#!/bin/sh

[ -n "$CMD" ] || CMD="python main.py 8.8.8.8 -c 4"

/scripts/run_tcpdump.sh client

# python main.py 
${CMD} 
STATUS=$?

sleep 0.3

exit $STATUS
