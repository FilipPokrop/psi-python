#!/bin/sh

CMD="python main.py"

/scripts/run_tcpdump.sh client

# python main.py 
${CMD} 
STATUS=$?

sleep 0.3

exit $STATUS
