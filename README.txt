
############################################################################################### 
Code to reproduce the results, and precomputed results, presented in Paper ## 8284 ##

## Paper title ## "Considering Theory of Mind in Human-Aware Task Planning for a Collaborative Robot"
###############################################################################################

This file describes the results format and how to reproduce them by executing some given scripts.
All produced results are stored in 'domains_and_results/results/'. (overwrite existing results!)

All results discussed in the paper are already precomputed and stored in 'domains_and_results/precomputed_results/'. 
Due to size limitation, the image of plans discussed in the Quantitative Analysis were removed, only the textual log files are given.

%%%%%%%%%%%%%%%%
% INSTALLATION %
%%%%%%%%%%%%%%%%

Before running experiments the planner and its dependencies have to be installed. 
Three dependencies have to be installed:
    $ apt install python3-distutils
    $ pip install catkin_pkg
    $ pip install graphviz
Then the planner itself needs to be installed with a script from the main folder:
    $ cd HATPEHDA/
    $ ./install.sh

%%%%%%%%%%%%%%%%%
% RESULT FORMAT %
%%%%%%%%%%%%%%%%%

Each planning problem is defined by the following parameters:
    - dom: the name of the domain considered (['cooking_pasta', 'box_prepare', 'car_maintenance'])
    - n: a unique initial state configuration identified by a number between 0 and 511. 

The solver used is described with the following parameters:
    - with_c: a parameter indicating if we are using the old or the new solver ("with_c" means 'with the contribution' corresponding to the new solver, respectively "without_c" means 'without the contribution' corresponding to the old solver)
    - with_d: a parameter indicating if we are using DELAYs to tackle relevant divergence, with the new solver ("with_d": 'with delay', nothing: without delay)

Each solved planning problem (planning problem + solver) produces some files:
    - 'n-with(out)_c(_with_d).txt': a text file with all detailed logs produced when computing the plan. The last line gives the list of possible plans separated with '/' if the planning was successful.
    - 'n-with(out)_c(_with_d).png': an image depicting the plans obtained. This file is generated only if the planning was successful.

Each planning problem is, by default, solved with both the old and the new solver (which may be using the DELAY feature).
Hence, solving a planning problem produces a pair of log files (for old and new solvers), and each log file can have an associated image file if the planning is successful.  

%%%%%%%%%%%%%%%%%%%%%%%
% RUNNING EXPERIMENTS %
%%%%%%%%%%%%%%%%%%%%%%%

Experiment:
    - Considering a given domain name, either only one or 512 different initial states are solved (either n=i or n=[0 to 511]).
    - A summarizing text file 'run.txt' is produced. It is (mostly) for quantitative analysis to obtain average values. The last line summarises the results in a format similar to the lines from Table 1 given in the paper. It shows for the old solver the success rate (S), the ratio of failed plans due to non-applicable action (NA), and the ratio of failed plans due to an inactivity deadlock case (IDL). For our solver, the success rate (S) (always 100%) and the ratio of successful plans, including a communication action. The ratio of plans where a non-relevant belief divergence remains after the execution is given under 'non_rel_div' (car domain). 

Running:
    - There is a bash script file for each experiment presented in the paper. Executing the desired script will run the corresponding experiment and produce its associated results. To execute a script, you must be in the main folder (cd HATPEHDA/) and to run the desired file (./script.sh).
    - When running an experiment, results (set of log text files and images, and run.txt file) are stored in the folder 'domains_and_results/results/', while the existing results already stored there are overwritten.
    
Here is the list of scripts and their associated experiments:
(Main paper)
    (Qualitative Analysis)
        - Scenario A => run_cook_scenario_A.sh
            Results in: '73-with_c.png' and '73-without_c.png'
        - Scenario B => run_cook_scenario_B.sh
            Results in '9-with_c.png' and '9-without_c.png'.
    (Quantitative Analysis, 512 init states each)
        - cooking_pasta domain () => run_full_cook_domain.sh 
            Results in 'run.txt' (S, NA, IDL, Com)
        - box_prepare domain => run_full_box_domain.sh
            Results in 'run.txt' (S, NA, IDL, Com)
        - car_maintenance domain => run_full_car_domain.sh
            Results in 'run.txt' (S, NA, IDL, Com, non_rel_div)
(Appendix)
    (Qualitative Analysis)
        - Scenario A => run_cook_appendix_scenario_A.sh 
            Results in '72-with_c.png' and '72-without_c.png'
        - Scenario B => run_cook_scenario_A.sh 
            Results in '73-with_c.png' and '73-without_c.png'.
        - Scenario C => run_cook_scenario_B.sh 
            Results in '9-with_c.png' and '9-without_c.png'.
        - Delaying example => run_delay_example.sh 
            Results in file '91-with_c_with_d.png'.