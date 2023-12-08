#!/usr/bin/env python3

import subprocess
import time 
import sys
import os

count_results = {   
                    "with_c":{"success":[], "failed":[], "with_com":[], "h_wait":[], "non_rel_div":[], "delayed":[]},
                    "without_c":{"success":[], "h_wait":[], "failed":[], "rna":[], "idl":[], "other":[]}
                }

# 9 attributes:
#   - 5 shared values
#   - 3 human values
#   - 1 starting agent
MAX = 9
total = 2**MAX

# Get domain name
domain_list = ["cooking_pasta", "box_prepare", "car_maintenance"]
if len(sys.argv) < 3:
    raise Exception("Missing arguements! (domain_name in {}, with_delay \"with_d\", optionnal single one id)".format(domain_list))
domain = sys.argv[1]
if domain not in domain_list:
    raise Exception("Domain name unknown! ({}, has to be in {})".format(domain, domain_list))
g_with_delay = sys.argv[2]

only_one = None
if len(sys.argv)>3 and sys.argv[3]!="no":
    only_one = int(sys.argv[3])

results = "Domain name : {}".format(domain)


# only_one = 0


cd_domains = "domains_and_results/"
cd_results = cd_domains + "results/"

call_durations = [1 for i in range(10)]


def print_time(t):
    if t>60:
        nb_min = int(t/60)
        nb_sec = int(t%60)
        return "{}min{}s".format(nb_min, nb_sec)

    else:
        nb_sec = int(10*t)/10
        return "{}s".format(nb_sec)

def get_ratio(up, down):
    return 0 if down==0 else int(10000*up/down)/100

def run_test(with_contrib="with_c", with_graph="with_g", with_delay=""):
    global count_results, call_durations
    for i in range(total):
        ETA_str=""
        ETA_bis_str=""

        if only_one != None:
            i = only_one

        n = i+1 if with_contrib=="with_c" else total+i+1
        progress = int(1000*n/(total*2))/10
        time_spent = int(10*(time.time()-start_time))/10
        
        ETA = int((2*total)*time_spent/n-time_spent)
        ETA_str = "ETA={}".format(print_time(ETA))

        t_1 = time.time()
        mean = 0
        for d in call_durations:
            mean += d
        mean = mean/len(call_durations)
        ETA_bis = int(mean * ((2*total)-n))
        ETA_bis_str = "ETA_bis={}".format(print_time(ETA_bis))

        str_delay = ""
        if with_delay == "with_d":
            str_delay = "_with_d"
        print("# Start run {}-{}{} (progress={}%) {} {} {}".format(i, with_contrib, str_delay, progress, print_time(time_spent), ETA_str, ETA_bis_str))

        f = open(cd_results+"{}-{}{}.txt".format(i, with_contrib, str_delay), "w")
        process = subprocess.Popen(["python3", cd_domains+domain+".py", with_contrib, with_graph, with_delay, str(i)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = process.communicate()
        stdout = stdout.decode('UTF-8')
        stderr = stderr.decode('UTF-8')

        treat_output(stdout, stderr, with_contrib, i)

        f.write(stdout)
        f.write(stderr)
        f.close()
        print("\tEnd {}-{}\n".format(i, with_contrib))
        if only_one!=None:
            break
        
        t_2 = time.time()
        dur = t_2-t_1
        call_durations = [dur] + call_durations[:-1]

def treat_output(stdout, stderr, with_contrib, i):
    error = stderr!=""
    if error:
        print("\t=> FAILED <=")
        count_results[with_contrib]["failed"].append(i)

        if with_contrib=="without_c":
            if stderr[-4:-1] == "RNA":
                print("\tRNA")
                count_results["without_c"]["rna"].append(i)
            elif stderr[-4:-1] == "IDL":
                print("\tIDL")
                count_results["without_c"]["idl"].append(i)
            else:
                count_results["without_c"]["other"].append(i)
    else: # No error
        count_results[with_contrib]["success"].append(i)

        index_non_rel_div = stdout.find("Non relevant div:\n") + len("Non relevant div:\n")
        non_rel_div = stdout[index_non_rel_div : stdout.find("\n", index_non_rel_div)]
        # index_plans = stdout.find("Filtered Plans:\n", index_non_rel_div) + len("Filtered Plans:\n")
        index_plans = stdout.find("Plans:\n", index_non_rel_div) + len("Plans:\n")
        plans = stdout[index_plans : stdout.find("\n", index_plans)]

        if with_contrib=="with_c":
            if "COM_ALIGN" in plans:
                print("\tCOM")
                count_results["with_c"]["with_com"].append(i)
            elif "DELAY" in plans:
                print("\tDelayed")
                count_results["with_c"]["delayed"].append(i)
            if non_rel_div=="True":
                print("\tNon rel div")
                count_results["with_c"]["non_rel_div"].append(i)
        if "HP-WAIT" in plans:
            print("\tH-WAIT")
            count_results[with_contrib]["h_wait"].append(i)

###################
### START TESTS ###
###################
start_time = time.time()
with_graph = "with_g"
with_delay = g_with_delay
os.system("rm {}*".format(cd_results))
run_test(with_contrib="with_c", with_graph=with_graph, with_delay=with_delay)
run_test(with_contrib="without_c", with_graph=with_graph)
end_time = time.time()
elapsed_time = int((end_time - start_time)*100)/100
results+= "\nElasped time = {}s\n".format(elapsed_time)
###################
#### END TESTS ####
###################

## With_c ##
nb_failed_with = len(count_results["with_c"]["failed"])
nb_success_with = (total-nb_failed_with)
ratio_success_with = get_ratio(nb_success_with, total)

nb_with_com = len(count_results["with_c"]["with_com"])
ratio_success_with_com = get_ratio(nb_with_com, nb_success_with)

nb_with_h_wait = len(count_results["with_c"]["h_wait"])
ratio_sucess_with_h_wait = get_ratio(nb_with_h_wait, nb_success_with)

nb_with_non_rel_div = len(count_results["with_c"]["non_rel_div"])
ratio_with_non_rel_div = get_ratio(nb_with_non_rel_div, nb_success_with)

nb_with_delayed = len(count_results["with_c"]["delayed"])
ratio_with_delayed = get_ratio(nb_with_delayed, nb_success_with)

## Without_c ##
nb_failed_without = len(count_results["without_c"]["failed"])
nb_success_without = len(count_results["without_c"]["success"])
ratio_success_without = get_ratio(nb_success_without, total)

nb_without_h_wait = len(count_results["without_c"]["h_wait"])
ratio_without_h_wait = get_ratio(nb_without_h_wait, nb_success_without)

nb_failed_without_rna = len(count_results["without_c"]["rna"])
ratio_failed_wo_rna = get_ratio(nb_failed_without_rna, nb_failed_without)

nb_failed_without_idl = len(count_results["without_c"]["idl"])
ratio_failed_wo_idl = get_ratio(nb_failed_without_idl, nb_failed_without)

nb_failed_without_other = len(count_results["without_c"]["other"])
ratio_failed_wo_other = get_ratio(nb_failed_without_other, nb_failed_without)

results+= "\n=> DETAILED RESULTS <=:"
results+= "\nCount (total={}) = ".format(total)
results+= "\n\twith({} fail - {}% success) =".format(nb_failed_with, ratio_success_with)
results+= "\n\t\twith_com({}- {}%) = {}".format(nb_with_com, ratio_success_with_com, count_results["with_c"]["with_com"])
results+= "\n\t\th_wait({}- {}%) = {}".format(nb_with_h_wait, ratio_sucess_with_h_wait, count_results["with_c"]["h_wait"])
results+= "\n\t\tnon_rel_div({}- {}%) = {}".format(nb_with_non_rel_div, ratio_with_non_rel_div, count_results["with_c"]["non_rel_div"])
results+= "\n\t\tdelayed({}- {}%) = {}".format(nb_with_delayed, ratio_with_delayed, count_results["with_c"]["delayed"])
results+= "\n\t\tfailed({}) = {}".format(nb_failed_with, count_results["with_c"]["failed"])
results+= "\n\twithout({} fail- {}% success): ".format(nb_failed_without, ratio_success_without)
results+= "\n\t\tsuccess({}) = {}".format(nb_success_without, count_results["without_c"]["success"])
results+= "\n\t\th_wait({}- {}%) = {}".format(nb_without_h_wait, ratio_without_h_wait, count_results["without_c"]["h_wait"])
results+= "\n\t\trna({}- {}%) = {}".format(nb_failed_without_rna, ratio_failed_wo_rna, count_results["without_c"]["rna"])
results+= "\n\t\tidl({}- {}%) = {}".format(nb_failed_without_idl, ratio_failed_wo_idl, count_results["without_c"]["idl"])
results+= "\n\t\tother({}- {}%) = {}".format(nb_failed_without_other, ratio_failed_wo_other, count_results["without_c"]["other"])
results+= "\n"
results+= "\n=> SHORT RESULTS <="
results+= "\n {}: Old Solver: S={}% NA={}% IDL={}% Our Solver: S={}% Com={}%".format(domain, ratio_success_without, ratio_failed_wo_rna, ratio_failed_wo_idl, ratio_success_with, ratio_success_with_com)

print(results)

f = open(cd_results+"run.txt", "w")
f.write(results)
f.close()
