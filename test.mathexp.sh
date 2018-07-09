#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python3 generate_reject.py ../pychains/subjects/mathexpr.py 10; done ) 2>mathexpr.err | tee mathexpr.log

trap times EXIT