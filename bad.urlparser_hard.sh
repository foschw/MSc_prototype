#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python3 generate_reject.py ../pychains/subjects/urlparser_hard.py 10; done ) 2>urlparser_hard.err | tee urlparser_hard.log

trap times EXIT
