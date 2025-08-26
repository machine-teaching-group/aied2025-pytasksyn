import os
import json
import argparse
from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# make all the fonts bigger
plt.rcParams.update({'font.size': 16})
from .utils import check_passed_all_tests, get_coverage, get_perc_passed_tests
from scipy.stats import norm
import numpy as np
from scipy.stats import truncnorm
from scipy.stats import kendalltau
# set all seeds
import random
from matplotlib.colors import ListedColormap, BoundaryNorm
from sklearn.metrics import cohen_kappa_score
np.random.seed(200)
from scipy.stats import ttest_ind
import csv

# Get the directory of the current script
script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
with open(os.path.join(parent_dir, 'data', 'model_configuration.json'), 'r') as f:
    model_configuration = json.load(f)

TUTOR_TESTSUITE_PASS_THRESHOLD = model_configuration['tutor_testsuite']['pass_threshold']
TUTOR_TESTSUITE_COVERAGE_THRESHOLD = model_configuration['tutor_testsuite']['coverage_threshold']
STU_PASS_THRESHOLD = model_configuration['student']['pass_threshold']

# set font size
plt.rcParams.update({'font.size': 50})
# set latex font
plt.rc('text', usetex=True)

# Get the directory of the current script
script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
ON_HEROKU = eval(os.environ.get("ON_HEROKU"))

def analyze_results(trial_path):
    data_df = pd.DataFrame(columns=['task', 'total_num_tc', 'gen_consistency', 'LLMJudge', 'Q-Testsuite', 'Q-Context', 'total_num_stu', 'num_passed_stu', 'passed_stus'])

    tasks = [folder for folder in os.listdir(trial_path) if os.path.isdir(os.path.join(trial_path, folder))]
    # sort by number
    tasks.sort(key=lambda x: int(x.split('_')[1]))
    for task in tasks:
        if not os.path.isdir(os.path.join(trial_path, task)):
            continue
        print(f'\n=== Analyzing task {task}')
        task_path = os.path.join(trial_path, task)
        # load pytest_report.json
        
        try:
            # === Judge
            judge_path = os.path.join(task_path, 'simulated_judges')
            if os.path.exists(judge_path):
                judge_q_overall_scores = []
                for judge in os.listdir(judge_path):
                    judge_path = os.path.join(judge_path, judge)
                    with open(os.path.join(judge_path, 'annotations.json'), 'r') as f:
                        annotations = json.load(f)
                    judge_q_overall_scores.append(annotations['q_overall'])
                if all(score == 1 for score in judge_q_overall_scores):
                    judge_q_overall = 1
                else:
                    judge_q_overall = 0

            with open(os.path.join(task_path, 'pytest_report.json'), 'r') as f:
                sol_pytest_report = json.load(f)
            # load 
            tests = sol_pytest_report['tests']
            num_passed_stu = 0
            total_num_stu = 0
            sol_num_passed_tc = 0
            simta_q_context = 0
            simta_q_concepts = 0
            passed_stus = []
            matrix_df = None
            total_num_tc = 0
            # test_coverage = 0
            gen_consistency = 0
            print(f'Number of test cases in the solution: {len(tests)}')
            if len(tests) > 0:
                matrix_df = pd.DataFrame(columns=['Simulated student'] + [str(i) for i in range(len(tests))])
                total_num_tc = sol_pytest_report['summary']['total']
                
                sol_outcomes = [-1 for i in range(len(tests))]
                for i in range(len(tests)):
                    if 'call' in tests[i]:
                        if tests[i]['call']['outcome'] == 'passed':
                            sol_outcomes[i] = 1
                        elif tests[i]['call']['outcome'] == 'failed':
                            sol_outcomes[i] = 0
                matrix_df = pd.concat([matrix_df, pd.DataFrame([['Expert'] + sol_outcomes], columns=['Simulated student'] + [str(i) for i in range(len(tests))])])
                sol_num_passed_tc = sol_outcomes.count(1)
                gen_consistency = 1 if sol_num_passed_tc==total_num_tc else 0

            
            #=== TUTORs for TESTSUITE
            tutor_testsuite_path = os.path.join(task_path, 'simulated_tutors')
            perc_passed_ta = []
            coverage_ta = []

            if os.path.exists(tutor_testsuite_path):
                # load annotations.json
                for assistant in os.listdir(tutor_testsuite_path):
                    assistant_path = os.path.join(tutor_testsuite_path, assistant)
                    # load pytest_report.json
                    perc_passed_tests = get_perc_passed_tests(os.path.join(assistant_path, 'pytest_report.json'))
                    coverage = get_coverage(os.path.join(assistant_path, 'pytest_coverage_report.json'))
                    perc_passed_ta.append(perc_passed_tests)
                    coverage_ta.append(coverage)
                
                print('perc_passed_ta', perc_passed_ta)
                print('coverage_ta', coverage_ta)

            
            q_testsuite = 1.0 if all(score >= TUTOR_TESTSUITE_PASS_THRESHOLD for score in perc_passed_ta) and all(score >= TUTOR_TESTSUITE_COVERAGE_THRESHOLD for score in coverage_ta) else 0.0
            
            #=== TUTORs for Q-Context
            tutor_path = os.path.join(task_path, 'simulated_tutors')
            if os.path.exists(tutor_path):
                # load annotations.json
                simta_q_context_scores = []
                for assistant in os.listdir(tutor_path):
                    # there is only one teaching assistant for now
                    assistant_path = os.path.join(tutor_path, assistant)
                    with open(os.path.join(assistant_path, 'annotations.json'), 'r') as f:
                        annotations = json.load(f)
                    simta_q_context_scores.append(annotations['context_relevance'])

                if all(score == 1 for score in simta_q_context_scores):
                    simta_q_context = 1
            
            #=== Students
            stus_path = os.path.join(task_path, 'simulated_students')
            
            if os.path.exists(stus_path):
                print(stus_path)
                total_num_stu = len(os.listdir(stus_path))
                all_stus = os.listdir(stus_path)
                all_stus = sorted(all_stus, key = lambda x: int(x.split('_')[-1]))
                for stu in all_stus:
                    stu_path = os.path.join(stus_path, stu)
                    print("stu_path=", stu_path)
                    if not os.path.exists(os.path.join(stu_path, 'pytest_report.json')):
                        continue
                    with open(os.path.join(stu_path, 'pytest_report.json'), 'r') as f:
                        stu_pytest_report = json.load(f)
                    stu_tests = stu_pytest_report['tests']
                    print("len(stu_tests)=", len(stu_tests))
                    if len(stu_tests) > 0:
                        total_num_tc = max(total_num_tc, len(stu_tests))
                    if matrix_df is None and len(stu_tests) > 0:
                        total_num_tc = len(stu_tests)
                        matrix_df = pd.DataFrame(columns=['Simulated student'] + [str(i) for i in range(len(stu_tests))])
                        print(f'Number of test cases in the student: {len(stu_tests)}')
                    
                    stu_outcomes = [-1 for i in range(total_num_tc)]
                    print("stu_outcomes=", stu_outcomes)

                    for i in range(len(stu_tests)):
                        try:
                            if stu_tests[i]['call']['outcome'] == 'passed':
                                stu_outcomes[i] = 1
                            elif stu_tests[i]['call']['outcome'] == 'failed':
                                stu_outcomes[i] = 0
                        except:
                            stu_outcomes[i] = -1

                    print("stu_outcomes=", stu_outcomes)
                    matrix_df = pd.concat([matrix_df, pd.DataFrame([['SimSTU ' + stu.split("_")[-1]] + stu_outcomes], columns=['Simulated student'] + [str(i) for i in range(total_num_tc)])])

                    if 'passed' in stu_pytest_report['summary']:
                        if check_passed_all_tests(os.path.join(stu_path, 'pytest_report.json')): 
                        # and stu_coverage>=STU_COVERAGE_THRESHOLD:
                            num_passed_stu += 1
                            passed_stus.append(stu)

            data_df = pd.concat([data_df, pd.DataFrame([[task, total_num_tc, gen_consistency, judge_q_overall, q_testsuite, simta_q_context, total_num_stu, num_passed_stu, passed_stus]], columns=['task', 'total_num_tc', 'gen_consistency', 'LLMJudge',  'Q-Testsuite', 'Q-Context', 'total_num_stu', 'num_passed_stu', 'passed_stus'])])
            matrix_df.to_csv(os.path.join(task_path, 'test_matrix.csv'), index=False)

            try:
                print("matrix_df=", matrix_df)
                matrix_df.set_index('Simulated student', inplace=True)
                matrix_df = matrix_df[matrix_df.columns].astype(float)

                if matrix_df.empty:
                    continue
                
                # Define the colormap for the values
                colors = ListedColormap(['grey', 'orangered', 'dodgerblue'])

                # Define boundaries for each value
                bounds = [-1.5, -0.5, 0.5, 1.5]  # Boundaries between each value (-1, 0, 1)
                norm = BoundaryNorm(bounds, colors.N)  # Normalizer

                ax = sns.heatmap(matrix_df, cmap=colors, norm=norm, cbar=False, square=True,
                 linewidths=2, linecolor='white', xticklabels=True, yticklabels=True,
                 vmin=-1, vmax=1)
                plt.tick_params(left=False, bottom=False)
                ax.set_aspect("equal")
                plt.xlabel('Generated test cases')
                plt.ylabel('')                
                plt.tick_params(axis='both', which='major', labelsize=10, labelbottom = False, bottom=False, top = True, labeltop=True)
                ax.tick_params(length=0)
                plt.tight_layout()
                plt.savefig(os.path.join(task_path, 'test_matrix.pdf'))
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
    print(data_df)
    print('data_df', data_df)
    data_df.to_csv(os.path.join(trial_path, 'results.csv'), index=False)
    return data_df




