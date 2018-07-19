#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python generate_reject.py ./subjects/simple.py 1000; done ) 2>simple.err | tee simple.log

trap times EXIT
