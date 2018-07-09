#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python3 generate_reject.py ../pychains/subjects/urlpy.py 1000; done ) 2>urlpy.err | tee urlpy.log

trap times EXIT
