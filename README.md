# CSC445 Programming Project: Linear Program Solver

## Overview
This program is a basic linear program solver that uses the Simplex Method to solve linear programs in standard form. It reads input linear programs from standard input, and prints out whether they are infeasible, unbounded or optimal. If they are optimal, the optimal value and solution vector will also be printed.

## Technologies
For this program, I used:
- Python 3
- Git (Gitlab)
- UNIX commands

## Usage
To use this program, run the following command:
```sh
python3 lp_solver.py < [INPUT]
```
where `[INPUT]` is a linear program in standard form, separated only by whitespace. The first row should contain the objective function, with `n` values, and all subsequent rows should contain the given constraints, with `n + 1` values.

There is no error checking, so if an invalid input is given, the program will behave unexpectedly, and will most likely crash.

## Solver Implementation
This solver uses the dictionary-based Simplex Method to solve linear programs given in standard form. The basic flow is as follows:

1. The linear program is read in from standard input and converted into a dictionary, represented as a 2D list. A secondary list of indexes is also created, storing the `(x,y)` coordinates of the optimization and slack variables.
2. The initial dictionary is checked for infeasibility. If it is feasible, the program proceeds to use the Simplex Method. If the dictionary is initially infeasible, the Two-Phase-Dual-Primal Method (described in **_Extra Features_**) is run on the dictionary, using the dual to determine feasibility.
3. Entering and leaving variables are chosen using the Largest Increase Rule, which are then used to pivot values. If a degenerate dictionary is found (by checking that a dictionary has the same optimal value twice in a row), Bland's Rule is used instead, in an effort to prevent cycling.
4. The dictionary is then checked for unboundedness, using the leaving index to ensure that there is at least one non-positive value in the column. If there is none, the leaving index will be it's original invalid value of `X`, and the program will print `unbounded` and terminate.
5. The program then performs a pivot operation, switching the entering column with the leaving row. All other relevant values in the dictionary are also updated accordingly, with epsilon comparison and float truncation to ensure that floating-point errors do not hinder execution.
6. If there are no more non-positive coefficients in the objective function, `optimal` is printed followed by the optimal value, and the solution vector, the latter two being printed with 7 digits of precision (after the decimal point). Otherwise, the Simplex Method continues to run, repeating steps 3 - 5.

## Cycle Prevention
Largest Increase Rule is used to pick entering and leaving variables until a degenerate dictionary is found. If one is found, the program switches to using Bland's Rule to ensure that cycling does not occur, as it is known that Bland's Rule is immune to cycling.

## Extra Features
The following features from the *Programming Project* PDF have been implemented in this program:
- **Primal-Dual Methods:** Instead of solving the auxiliary linear program with proxy variable theta, the Two-Phase-Dual-Primal Method is used to find an initially feasible dictionary if it exists. The process is as follows:
    1. If a dictionary is found to be initially infeasible (non-positive slack variable values), the dual of the given dictionary is computed by taking the negative transpose of the dictionary.
    2. The objective function is then zero-ed out in the dual dictionary, with the original objective function being stored for later.
    3. The `solve` method is then used on the dual linear program with an objective function of `0x1 + 0x2 + ... + 0xn` to find the optimal dual dictionary.
    4. The `solve` method finds entering & leaving variables, and performs pivots, just as it would for the primal dictionary.
    5. If no leaving variable can be found, this indicates that the dual is unbounded, meaning the primal is infeasible, and so the program prints `infeasible` and terminates.
    6. If an optimal dual dictionary is found, the dual of the dual is taken to retrieve the new feasible primal dictionary. The modified primal objective function is then injected back into dictionary.
    7. Finally, the `solve` method completes the solving of the primal dictionary using the process outlined in **_Solver Implementation_**

## Organization Information
- The code is split into methods where possible such that they each have one purpose. In some cases, this was not done, as splitting some methods into smaller ones would have made the logic messier and harder to trace. This unfortunately lead to a bit of duplicated code; however, this was kept at a minimum.
- Constants are all stored at the top of the file so that modifying certain values is as easy as changing a single line. Also limits the amount of "magic numbers" found in the code.
- Several commonly used functions were made into utility methods at the top of the file (ex. `negate`) as this made simple operations easier to read.

## Author Information
**Author:** Nilay Sondagar

**Student ID:** V00889998

**Date Started:** July 10, 2021

**Date Submitted:** July 15, 2021