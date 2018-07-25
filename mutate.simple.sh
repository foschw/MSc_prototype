#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python generate_reject.py ./subjects/simple.py 1000 "rejected_simple.bin"; done ) 2>simple.err | tee simple.log
python find_mutation_lines.py subjects/simple.py "rejected_simple.bin" 1>simple.log 2>simple.err
python find_mutation_lines.py subjects/simpleloop.py "rejected_simple.bin" 1>simpleloop.log 2>simpleloop.err

trap times EXIT
