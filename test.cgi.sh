#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python3 generate_reject.py ../pychains/subjects/cgi.py 1000; done ) 2>cgi.err | tee cgi.log

trap times EXIT
