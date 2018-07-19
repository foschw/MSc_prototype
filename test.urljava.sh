#!/usr/bin/env bash
start=0$1
(for i in `seq $start 0`; do echo $i --------; env BFS=true R=$i P=U python generate_reject.py ../pychains/subjects/urljava.py 100; done ) 2>urljava.err | tee urljava.log

trap times EXIT
