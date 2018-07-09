#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python3 generate_reject.py ../pychains/subjects/microjson.py 1000; done ) 2>microjson.err | tee microjson.log

trap times EXIT
