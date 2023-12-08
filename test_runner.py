#!/usr/bin/env python3

from progress.bar import IncrementalBar
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

# sys.argv = ['/home/afavier/ws/HATPEHDA/test_runner.py', 'cooking_pasta', 'with_d', 65]

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

results = f"Domain name : {domain} - {g_with_delay}"


# only_one = 0


cd_domains = "domains_and_results/"
cd_results = cd_domains + "results/"


def get_ratio(up, down):
    return 0 if down==0 else int(10000*up/down)/100

def run_test(with_contrib="with_c", with_graph="with_g", with_delay=""):
    global count_results

    bar = IncrementalBar('Processing', max=total, suffix="%(percent).1f%% - %(elapsed_td)s - ETA=%(eta_td)s")
    for i in range(total):
        bar.next()
        print(" ")

        if only_one != None:
            i = only_one

        n = i+1 if with_contrib=="with_c" else total+i+1
        
        str_delay = ""
        if with_delay == "with_d":
            str_delay = "_with_d"
        print(f"# Start run {i}-{with_contrib}{str_delay}")

        f = open(cd_results+"runs/{}-{}{}.txt".format(i, with_contrib, str_delay), "w")
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
        
    bar.finish()

av_nb_com = 0.0
av_nb_h_wait = 0.0
av_length = 0.0
av_nb_delay = 0.0
nb_plans = 0

def treat_output(stdout, stderr, with_contrib, i):
    global av_nb_com, av_nb_h_wait, av_length, nb_plans, av_nb_delay

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
        index_plans = stdout.find("Plans:\n", index_non_rel_div) + len("Plans:\n")
        plans = stdout[index_plans : stdout.find("\n", index_plans)]

        # if with_contrib=="with_c":
        #     if "COM_ALIGN" in plans:
        #         print("\tCOM")
        #         count_results["with_c"]["with_com"].append(i)
        #     if "DELAY" in plans:
        #         print("\tDelayed")
        #         count_results["with_c"]["delayed"].append(i)
        #     if non_rel_div=="True":
        #         print("\tNon rel div")
        #         count_results["with_c"]["non_rel_div"].append(i)
        # if "HP-WAIT" in plans:
        #     print("\tH-WAIT")
        #     count_results[with_contrib]["h_wait"].append(i)

        index_metrics = stdout.find("best_metrics:\n", index_plans) + len("best_metrics:\n")
        metrics_str = stdout[index_metrics : stdout.find("\n", index_metrics)]
        splitted_metrics = metrics_str[1:-1].split(", ")
        nb_com      = float(splitted_metrics[0])
        nb_h_wait   = float(splitted_metrics[1])
        length      = float(splitted_metrics[2])
        nb_delay    = float(splitted_metrics[3])
        av_nb_com       += nb_com
        av_nb_h_wait    += nb_h_wait
        av_length       += length
        av_nb_delay     += nb_delay
        nb_plans += 1

        if with_contrib=="with_c":
            if nb_com>0:
                print("\tCOM")
                count_results["with_c"]["with_com"].append(i)
            if nb_delay>0:
                print("\tDelayed")
                count_results["with_c"]["delayed"].append(i)
            if non_rel_div=="True":
                print("\tNon rel div")
                count_results["with_c"]["non_rel_div"].append(i)
        if nb_h_wait>0:
            print("\tH-WAIT")
            count_results[with_contrib]["h_wait"].append(i)
        

###################
### START TESTS ###
###################
start_time = time.time()
with_graph = "with_g"
with_delay = g_with_delay
os.system(f"rm {cd_results}runs/*")
os.system(f"rm {cd_results}run.txt")
run_test(with_contrib="with_c", with_graph=with_graph, with_delay=with_delay)
# run_test(with_contrib="without_c", with_graph=with_graph)
end_time = time.time()
elapsed_time = int((end_time - start_time)*100)/100
results+= "\nElasped time = {}s\n".format(elapsed_time)
###################
#### END TESTS ####
###################

av_nb_h_wait/=nb_plans
av_nb_com/=nb_plans
av_length/=nb_plans
av_nb_delay/=nb_plans

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
results+= f"\n {av_nb_com}, {av_nb_h_wait}, {av_length}, {av_nb_delay}"

print(results)

f = open(cd_results+"run.txt", "w")
f.write(results)
f.close()
