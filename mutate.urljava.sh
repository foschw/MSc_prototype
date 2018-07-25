#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python generate_reject.py ../pychains/subjects/urljava.py 100 "rejected_urljava.bin"; done ) 2>urljava.err | tee urljava.log
python find_mutation_lines.py ../pychains/subjects/urljava.py "rejected_urljava.bin" 1>urljava.log 2>urljava.err

trap times EXIT
