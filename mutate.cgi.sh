#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python generate_reject.py ../pychains/subjects/cgi.py 1000 "rejected_cgi.bin" ; done ) 2>cgi.err | tee cgi.log
python find_mutation_lines.py ../pychains/subjects/cgi.py rejected_cgi.bin 1>cgi.log 2>cgi.err
trap times EXIT
