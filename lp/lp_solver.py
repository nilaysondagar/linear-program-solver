from sys import float_info, stdin
from re import split
from math import isclose, trunc

####################################################################
# CONSTANTS
####################################################################
COMPARISON_EPSILON = 0.0000001  # Delta for comparing floats
CSI = 1                         # Constraint start index in dictionary
CVI = 0                         # Constraint value index in constaint rows of dictionary
INFEASIBLE = 'infeasible'
INVALID_INDEX = 'X'
MAIN = '__main__'
OCI = 1                         # Objective constraint index in objective function row
OFI = 0                         # Objective function index in dictionary
OPTIMAL = 'optimal'
TRUNCATE_TO = 10                # Maximum decimals to store on a float
UNBOUNDED = 'unbounded'

####################################################################
# UTILITIES
####################################################################

# Negates the given number
def negate(num):
    return num * -1

# Determines if two floats are close enough to be considered equal
def is_close(a, b):
    return isclose(a, b, abs_tol=COMPARISON_EPSILON)

# Determines if two floats are not close enough to be considered equal
def is_not_close(a,b):
    return not is_close(a,b)

# Truncates floats to {TRUNCATE_TO} decimal places
def truncate(num):
    step = 10.0 ** TRUNCATE_TO
    return trunc(step * num) / step

# Either truncates the given number, or if it's equivalently 0, returns 0
def normalize(num):
    return (
        truncate(num)
        if abs(num) > COMPARISON_EPSILON
        else 0
    )

# Sorts naturally such that "x 2" comes before "x 12"
def natural_sort(array):
    convert = lambda l: int(l) if l.isdigit() else l
    natural_key = lambda d: [convert(val) for val in split('([0-9]+)', d["label"])]

    return sorted(array, key=natural_key)

# Takes the negative transpose of a primal dictionary to create the dual
def get_dual(dictionary):
    transposed = list(map(list, zip(*dictionary)))
    return [[negate(coeff) if is_not_close(coeff, 0) else 0 for coeff in row] for row in transposed]

# Returns the objective value of the given dictionary
def get_objective_value(dictionary):
    return dictionary[0][0]

# Extracts the solution coordinates from the given dictionary (x1, x2, ...)
def get_solution_vector(indexes, dictionary):
    nonbasic_vars = list(filter(lambda d: 'x' in d["label"], indexes))
    solution_vector = [dictionary[d["y"]][d["x"]] if d["y"] != 0 else 0 for d in nonbasic_vars]

    return solution_vector

# Prints float to 7 decimals, with no left padded zeros
def print_float(num, no_new_line=False):
    print(
        str(float('%.7g' % num)).rstrip('0').rstrip('.'),
        end=' ' if no_new_line else '\n'
    )

# DEBUGGING: Logs given dictionary in readable format with the given label
def log_raw_dictionary(dictionary, label='RAW DICTIONARY'):
    print(f'\n{label}')
    for row in dictionary:
        print(row)
    print()

# DEBUGGING: Logs the given dictionary's objective function and constraints
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

# Prints {INFEASIBLE}
def log_infeasible():
    print(INFEASIBLE)

# Prints {OPTIMAL}, followed by the optimal value and solution vector
def log_optimal(objective_value, location):
    print(OPTIMAL)
    print_float(objective_value)
    [print_float(coor, True) for coor in location]
    print()

# Prints {UNBOUNDED}
def log_unbounded():
    print(UNBOUNDED)

####################################################################
# METHODS
####################################################################

# Converts a given constraint from a LP to dictionary form
# (negates all coefficients, but not the constraint value)
def convert_constraints(constraint):
    new_constraint = [constraint[-1]]
    constraint = list(map(
        lambda x: negate(x) if x != 0 else x,
        constraint[:-1]
    ))
    new_constraint.extend(constraint)

    return new_constraint

# Reads in an LP from standard input and creates the corresponding
# dictionary
def extract_lp_from_stdin():
    # Read first line as list of floats for objective function
    objective_function = [0]
    objective_function.extend([float(coeff) for coeff in stdin.readline().strip().split()])

    # Read all other lines as lists of floats for constraints
    constraints = []
    for line in stdin.readlines():
        constraints.append([float(coeff) for coeff in line.strip().split()])

    # Negate all constraint coefficients
    constraints = list(map(convert_constraints, constraints))

    # Combine into a single 2D array
    dictionary = [objective_function] + constraints

    return dictionary

# Gets the next entering variable for the given dictionary,
# either using Largest Increase Rule or Bland's Rule
def get_entering(dictionary, indexes, is_degenerate, is_primal):
    zero_index = 'y' if is_primal else 'x'
    comp_index = 'x' if is_primal else 'y'

    # Pick entering via Largest Increase Rule
    if not is_degenerate:
        entering_val = max(dictionary[OFI][OCI:])
        entering_index = dictionary[OFI][OCI:].index(entering_val) + OCI
        return entering_index

    # Pick entering via Bland's Rule
    bland_indexes = natural_sort([dict for dict in indexes if dict[zero_index] == 0])
    for dict in bland_indexes:
        if dictionary[OFI][dict[comp_index]] > 0:
            entering_index = dict[comp_index]
            break

    return entering_index

# Gets the next leaving variable for the given dictionary,
# either using Largest Increase Rule or Bland's Rule
def get_leaving(dictionary, indexes, entering_index, is_degenerate, is_primal):
    zero_index = 'x' if is_primal else 'y'
    leaving_val = float_info.max
    leaving_index = INVALID_INDEX

    # Pick leaving via smallest bound on entering variable
    if not is_degenerate:
        for i, row in enumerate(dictionary[CSI:], start=CSI):
            if ((row[entering_index] < 0) and (negate(row[CVI] / row[entering_index])) < leaving_val):
                leaving_index = i
                leaving_val = normalize(negate(row[CVI] / row[entering_index]))

        return leaving_index

    # Pick leaving via Bland's Rule
    leaving_indexes = [dict for dict in indexes if dict[zero_index] == 0]
    possible_pivots = []

    for i, row in enumerate(dictionary[CSI:], start=CSI):
        if row[entering_index] < 0:
            possible_pivots.append({
                "index": i,
                "label_prefix": leaving_indexes[i - 1]["label"][:1],
                "label_index": int(leaving_indexes[i - 1]["label"][2:]),
                "val": normalize(negate(row[CVI] / row[entering_index]))
            })

    # Find the smallest, lowest indexed basic and slack variables
    possible_pivot_x = min(
        sorted(
            [dict for dict in possible_pivots if dict["label_prefix"] == 'x'],
            key=lambda k: k['label_index']
        ),
        key=lambda k: k["val"],
        default={"index": INVALID_INDEX, "val": float_info.max}
    )
    possible_pivot_z = min(
        sorted(
            [dict for dict in possible_pivots if dict["label_prefix"] == 'z'],
            key=lambda k: k['label_index']
        ),
        key=lambda k: k["val"],
        default={"index": INVALID_INDEX, "val": float_info.max}
    )

    # Choose the smallest and lowest indexed leaving variable out
    # of the two computed above
    leaving_dict = (
        possible_pivot_x
        if bool(possible_pivot_x) and possible_pivot_x['val'] < possible_pivot_z['val']
        else possible_pivot_z
    )
    leaving_index = leaving_dict["index"]

    return leaving_index

# Prints {UNBOUNDED} and exits if no valid leaving variable was found
def exit_if_unbounded(leaving_index):
    if leaving_index == INVALID_INDEX:
        log_unbounded()
        exit()

# Prints {INFEASIBLE} and exits if no valid leaving variable was found during initialization
def exit_if_infeasible(leaving_index):
    if leaving_index == INVALID_INDEX:
        log_infeasible()
        exit()

# Creates the index list of the location of original (x) and slack (z) variables
def create_indexes(dictionary):
    var_indexes = [({ "label": f'x {i}', "x": i, "y": 0 }) for i in range(1, len(dictionary[OFI]))]
    var_indexes.extend([({ "label": f'z {i}', "x": 0, "y": i }) for i in range(1, len(dictionary))])

    return var_indexes

# Creates the index list of the location of original (x) and slack (z) variables for the dual
# (values are flipped, so that when we go back to the primal, all the values are in the correct spot)
def create_dual_indexes(dictionary):
    var_indexes = [({ "label": f'z {i}', "x": 0, "y": i }) for i in range(1, len(dictionary[OFI]))]
    var_indexes.extend([({ "label": f'x {i}', "x": i, "y": 0 }) for i in range(1, len(dictionary))])

    return var_indexes

# Swaps two indexes as part of the pivot so we can keep track of variable locations
def swap_indexes(entering, leaving, indexes):
    entering_index = next((
        i for (i, dict) in enumerate(indexes)
        if dict["x"] == entering
    ))
    leaving_index = next((
        i for (i, dict) in enumerate(indexes)
        if dict["y"] == leaving
    ))

    indexes[entering_index].update({ "x": 0, "y": leaving })
    indexes[leaving_index].update({ "x": entering, "y": 0 })

    return indexes

# Swaps two indexes as part of the pivot so we can keep track of variable locations in the dual
# (values are flipped, so that when we go back to the primal, all the values are in the correct spot)
def swap_dual_indexes(entering, leaving, indexes):
    entering_index = next((
        i for (i, dict) in enumerate(indexes)
        if dict["y"] == entering
    ))
    leaving_index = next((
        i for (i, dict) in enumerate(indexes)
        if dict["x"] == leaving
    ))

    indexes[entering_index].update({ "x": leaving, "y": 0 })
    indexes[leaving_index].update({ "x": 0, "y": entering })

    return indexes

# Injects the objective function into the dictionary (replaces the first row)
def inject_objective(dictionary, objective):
    for i in range(len(dictionary)):
        dictionary[i][0] = objective[i]

    return dictionary

# Extracts the objective function into the dictionary (replaces the first row with all 0s)
def extract_objective(dictionary):
    objective = []

    for i in range(len(dictionary)):
        objective.append(dictionary[i][0])
        dictionary[i][0] = 0

    return [dictionary, objective]

# Used the Two-Phase-Primal-Dual method to find a feasible primal dictionary
# using the dual when the dictionary is initially infeasible
def handle_initially_infeasible(dictionary, indexes):
    # Check for negative values
    if any([row[0] < 0 for row in dictionary[1:]]):
        objective_func = dictionary[0]

        # Zero out the objective function
        dictionary[0] = [0 for i in range(len(dictionary[0]))]
        dictionary = get_dual(dictionary)

        # Find the optimal dual dictionary if it exists
        [optimal_dual, var_indexes, feasible_objective_func] = solve(dictionary, objective_func)

        # Reconstruct the primal dictionary, now feasible
        feasible_primal = get_dual(optimal_dual)
        feasible_primal[0] = feasible_objective_func
        return [feasible_primal, var_indexes]

    return [dictionary, indexes]

# Performs a pivot operation on the dictionary, swapping a row and column
# using the {entering_index} and {leaving_index}
def pivot(dictionary, entering_index, leaving_index):
    # Get pivot location
    pivot_point = dictionary[leaving_index][entering_index]

    # Divide all coefficients in the leaving row by the pivot value
    dictionary[leaving_index] = [coeff / pivot_point for coeff in dictionary[leaving_index]]

    # Calculate new coefficients for each row in the dictionary
    for i in range(len(dictionary)):
        if i != leaving_index:
            pivot_row = []
            dic_row = []

            for coeff in dictionary[leaving_index]:
                pivot_row.append(normalize(coeff * dictionary[i][entering_index]))

            for index, (x, y) in enumerate(zip(dictionary[i], pivot_row)):
                dic_row.append(
                    normalize(x - y)
                    if index != entering_index
                    else normalize(x / pivot_point)
                )

            dictionary[i] = dic_row

    dictionary[leaving_index] = [negate(coeff) for coeff in dictionary[leaving_index]]
    dictionary[leaving_index][entering_index] = normalize(dictionary[leaving_index][entering_index] / negate(pivot_point))

    return dictionary

# Attempts to solve a linear program given its dictionary
def solve(dictionary, dual_objective=None):
    is_primal = dual_objective == None
    is_degenerate = False
    last_objective_value = 0
    var_indexes = (
        create_indexes(dictionary)
        if is_primal
        else create_dual_indexes(dictionary)
    )

    # Check if the dictionary is initially infeasible, and if it is,
    # make it feasible (if possible)
    if is_primal:
        [dictionary, var_indexes] = handle_initially_infeasible(dictionary, var_indexes)

    # Run the Simplex Method, finding entering & leaving variables and performing pivots
    # in an attempt to find an optimal solution
    while any(coeff > 0 for coeff in dictionary[OFI][OCI:]):
        entering_index = get_entering(dictionary, var_indexes, is_degenerate, is_primal)
        leaving_index = get_leaving(dictionary, var_indexes, entering_index, is_degenerate, is_primal)

        # Check for unboundedness and infeasibility
        if is_primal:
            exit_if_unbounded(leaving_index)
        else:
            exit_if_infeasible(leaving_index)

        # If solving the dual, inject the objective function back in so that
        # the pivot operation can correctly modify the objective function for
        # when we need to convert back to primal. Then extract back out after
        # the pivot is complete
        if not is_primal:
            dictionary = inject_objective(dictionary, dual_objective)

        dictionary = pivot(dictionary, entering_index, leaving_index)

        if not is_primal:
            [dictionary, dual_objective] = extract_objective(dictionary)

        # Update x and z variable indexes
        var_indexes = (
            swap_indexes(entering_index, leaving_index, var_indexes)
            if is_primal
            else swap_dual_indexes(entering_index, leaving_index, var_indexes)
        )

        # Switch to Bland's Rule if degeneracy is found, to prevent cycling
        is_degenerate = is_degenerate or (is_close(last_objective_value, dictionary[OFI][0]))
        last_objective_value = dictionary[OFI][0]

    return (
        [get_objective_value(dictionary), get_solution_vector(var_indexes, dictionary)]
        if is_primal
        else [dictionary, var_indexes, dual_objective]
    )

####################################################################
# MAIN
####################################################################

# Solve the given Linear Program
def lp_solver():
    dictionary = extract_lp_from_stdin()

    [optimal_value, solution_vector] = solve(dictionary)
    log_optimal(optimal_value, solution_vector)

if __name__ == MAIN:
    lp_solver()
