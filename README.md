The easiest way to try existing domains is through the test_runner.py script.
It takes as arguments firs the domain name (cooking_pasta, box_prepare, car_maintenance)
Then if the delay feature should be use, write "with_d" to enable it, and "without_d" to do without.
Finally, use can add a Id to run the corresponding configuration. Not providing this argument will run sequentially all possible configuration (512 runs).

All results are stored in domains_and_results/results/. A full log report is stored as "run.txt" and all runs are stored in domains_and_results/results/runs/. Each run has a picture of the solution tree and its associated text log file.


You can also directly run the domain python file with the following command:
python domains_and_results/*domain_name*.py [with_contrib] [with_graph] [with_delay] [n]
4 arguments:
- with_contrib: "with_c" enables the contribution (use of ToM), "without_c" disables it, very close to ICRA22 submission planning process.
- with_graph: "with_g" enables computing the picture of the solution tree, "without_g" disables it.
- with_delay: "with_d" enables the delay feature, "without_d" disables it.
- n: integer number from 0 to 511 corresponding to problem (pair of initial beliefs).