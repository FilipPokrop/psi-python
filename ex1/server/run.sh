#!/bin/sh

[ -n "$CMD" ] || CMD="python main.py"

/scripts/run_tcpdump.sh server 

# python main.py 
${CMD} 
STATUS=$?

sleep 0.3

exit $STATUS
