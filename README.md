# MSc_prototype
Prototype for my master thesis,
Usage: 
0. Install pychains (https://github.com/vrthra/pychains) and "pip install astunparse" (requires python 3.6 until updated) as well as "pip install pudb"
1. Get some test subjects (e.g. the ones from pychains which the scripts refere to)
2. either run a test script (test.cgi.sh etc) or "python generate_reject.py path/to/script.py" number_of_pychain_iterations
3. After a rejected.bin file is created run "python find_mutation_lines.py path/to/script.py" or "python find_mutation_lines.py path/to/script.py "path/to/rejected.bin""
