from sys import argv, float_info

####################################################################
# CONSTANTS
####################################################################
CVI = 0 # Constraint value index in constaint rows of dictionary
CSI = 1 # Constraint start index in dictionary
INFEASIBLE = 'infeasible'
INVALID_INDEX = 'X'
MAIN = '__main__'
OCI = 1 # Objective constraint index in objective function row
OFI = 0 # Objective function index in dictionary
OPTIMAL = 'optimal'
READ_PERMISSION = 'r'
UNBOUNDED = 'unbounded'

####################################################################
# UTILITIES
####################################################################

def negate(el):
    return el * -1

def print_float(num, no_new_line=False):
    # print('{:.7f}'.format(num), end=' ' if no_new_line else '\n')
    print('%s' % float('%.7g' % num), end=' ' if no_new_line else '\n')

def log_raw_dictionary(dictionary):
    print('\nRAW DICTIONARY')
    for row in dictionary:
        print(row)
    print()

def log_lp(dictionary):
    print('OBJECTIVE FUNCTION:')
    print(dictionary[OFI])
    print()

    print('CONSTRAINTS:')
    for num in dictionary[CSI:]:
        print('[', end='')
        for i in num:
            print_float(i, no_new_line=True)
        print(']')

def log_infeasible():
    print(INFEASIBLE)

def log_optimal(objective_value, location):
    print(OPTIMAL)
    print_float(objective_value)
    [print_float(coor, True) for coor in location]
    print()

def log_unbounded():
    print(UNBOUNDED)

####################################################################
# METHODS
####################################################################

def convert_constraints(constraint):
    new_constraint = [constraint[-1]]
    constraint = list(map(lambda x: negate(x) if x != 0 else x, constraint[:-1]))
    new_constraint.extend(constraint)
    return new_constraint

def extract_lp_from_file(filename):
    file = open(filename, READ_PERMISSION)

    # Read first line as list of floats for objective function
    objective_function = [0]
    objective_function.extend([float(coeff) for coeff in file.readline().strip().split()])

    # Read all other lines as lists of floats for constraints
    constraints = []
    for line in file:
        constraints.append([float(coeff) for coeff in line.strip().split()])

    # Negate all constraint coefficients
    constraints = list(map(convert_constraints, constraints))

    # Combine into a single 2D array
    dictionary = [objective_function] + constraints

    return dictionary

def get_entering(dictionary):
    entering_val = max(dictionary[OFI][OCI:])
    entering_index = dictionary[OFI].index(entering_val)
    return [entering_index, entering_val]

def get_leaving(dictionary, entering_index):
    leaving_val = float_info.max
    leaving_index = INVALID_INDEX

    for i, row in enumerate(dictionary[CSI:], start=CSI):
        if ((row[entering_index] < 0) and (negate(row[CVI] / row[entering_index])) < leaving_val):
            leaving_index = i
            leaving_val = negate(row[CVI] / row[entering_index])

    return [leaving_index, leaving_val]

def get_objective_value(dictionary):
    return dictionary[0][0]

def exit_if_unbounded(leaving_index):
    if leaving_index == INVALID_INDEX:
        log_unbounded()
        exit()

def pivot(dictionary, entering_index, leaving_index):
    pivot_point = dictionary[leaving_index][entering_index]
    dictionary[leaving_index] = [coeff / pivot_point for coeff in dictionary[leaving_index]]

    for i in range(len(dictionary)):
        if i != leaving_index:
            pivot_row = [coeff * dictionary[i][entering_index] for coeff in dictionary[leaving_index]]
            dictionary[i] = [x - y for x, y in zip(dictionary[i], pivot_row)]

    dictionary[leaving_index] = [negate(coeff) for coeff in dictionary[leaving_index]]

    return dictionary

def solve(dictionary):
    while any(coeff > 0 for coeff in dictionary[OFI][OCI:]):
        [entering_index, entering_val] = get_entering(dictionary)
        print('Entering', entering_index, ':', entering_val)

        [leaving_index, leaving_val] = get_leaving(dictionary, entering_index)
        print('Leaving', leaving_index, ':', dictionary[leaving_index][entering_index], '(pivot point) =', leaving_val)

        exit_if_unbounded(leaving_index)
        print()

        dictionary = pivot(dictionary, entering_index, leaving_index)

    return get_objective_value(dictionary)


####################################################################
# MAIN
####################################################################

def lp_solver():
    filename = argv[1]
    dictionary = extract_lp_from_file(filename)
    solution = solve(dictionary)
    log_optimal(solution, [1.45743853499, 2, 3])

if __name__ == MAIN:
    lp_solver()
