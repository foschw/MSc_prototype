#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python generate_reject.py ../pychains/subjects/microjson.py 1000 "rejected_microjson.bin"; done ) 2>microjson.err | tee microjson.log
python find_mutation_lines.py ../pychains/subjects/microjson.py "rejected_microjson.bin" 1>microjson.log 2>microjson.err
trap times EXIT
