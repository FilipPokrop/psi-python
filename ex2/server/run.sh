#!/bin/sh

CMD="python main.py"

ls /
ls /scripts

/scripts/run_tcpdump.sh server 

# python main.py 
${CMD} 
STATUS=$?

sleep 0.3

exit $STATUS
