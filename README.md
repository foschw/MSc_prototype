# MSc_prototype
Prototype for my master thesis,
Usage: 
0. Install pychains (https://github.com/vrthra/pychains) and "pip install astunparse" (requires python 3.6 until updated) as well as "pip install pudb" or use the docker version.
1. Get some test subjects (e.g. the ones from pychains which the scripts refere to)
2. run "python py_mauris.py path_to_py.py (-t approximate allowed input generation time in seconds)"
2.1 if you want to save the console output append "> >(tee -a stdout.log) 2> >(tee -a stderr.log >&2)" (stdout + stderr) or "| tee output.log" (stdout only) to the command
3. you can repeat a run with a valid .bin file by using the -b parameter and also set the random seed with -s
