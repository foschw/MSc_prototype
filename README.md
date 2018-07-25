# MSc_prototype
Prototype for my master thesis,
Usage: 
0. Get some test subjects (e.g. the ones from https://github.com/vrthra/pychains which the scripts refere to)
1. either run a test script (test.cgi.sh etc) or "python generate_reject.py path/to/script.py" number_of_pychain_iterations
2. After a rejected.bin file is created run "python find_mutation_lines.py path/to/script.py" or "python find_mutation_lines.py path/to/script.py "path/to/rejected.bin""
