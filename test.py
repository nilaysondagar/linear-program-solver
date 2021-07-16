from sys import argv
import subprocess

OUTPUT_PATH = '../tests/output'
INPUT_PATH = '../tests/input'
LP_SOLVER_PATH = '../lp/lp_solver.py'

start_index = 1
end_index = 78

if argv[1] == '445':
    end_index = 2
if argv[1] == 'netlib':
    start_index = 3
    end_index = 16
elif argv[1] == 'vander':
    start_index = 17
    end_index = 32
elif argv[1] == 'extra':
    start_index = 33
elif int(argv[1]) in range(start_index, end_index + 1):
    start_index = int(argv[1])
    end_index = int(argv[1])

print(f'Running test {start_index} to {end_index}...\n\n')

for i in range(start_index, end_index + 1):
    output = open(f'{OUTPUT_PATH}/test_output{i}.txt')
    input = open(f'{INPUT_PATH}/test_input{i}.txt')

    print(f'EXPECTED for test {i}:')
    print(output.read())
    print(f'ACTUAL for test {i}:')
    process = subprocess.Popen(["python3", LP_SOLVER_PATH], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    print(process.communicate(input=input.read().encode())[0].decode())
    process.stdin.close()
    print('--------------------------------------------------------')
    print()
