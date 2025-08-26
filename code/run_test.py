import os
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import random
import subprocess
from .utils import check_passed_all_tests, get_coverage, get_perc_passed_tests


# set all seeds
np.random.seed(1)
random.seed(1)

# Get the directory of the current script
script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
ON_HEROKU = eval(os.environ.get("ON_HEROKU", "False"))
MAX_WORKERS = 20 if ON_HEROKU else min(32, os.cpu_count() + 4)

with open(os.path.join(parent_dir, 'data', 'model_configuration.json'), 'r') as f:
    model_configuration = json.load(f)
TUTOR_TESTSUITE_PASS_THRESHOLD = model_configuration['tutor_testsuite']['pass_threshold']
TUTOR_TESTSUITE_COVERAGE_THRESHOLD = model_configuration['tutor_testsuite']['coverage_threshold']
STU_PASS_THRESHOLD = model_configuration['student']['pass_threshold']
STU_COVERAGE_THRESHOLD = model_configuration['student']['coverage_threshold']
STU_POPULATION_SIZE = model_configuration['student']['quantity']
STU_POPULATION_PASSING_THRESHOLD = model_configuration['student']['population_passing_threshold']

def test_student(stu_folder, task_folder):
    test_suite_stu_path = os.path.join(stu_folder, 'test_suite_stu.py')
    task_suite_path = os.path.join(task_folder, 'test_suite.py')
    
    with open(task_suite_path, 'r') as f:
        test_suite_content = f.read().replace('from solution import', 'from solution_program import')
    
    with open(test_suite_stu_path, 'w') as f:
        f.write("from solution_program import *\n" + test_suite_content)

    test_results_file_path = os.path.join(stu_folder, 'test_results.txt')
    pytest_coverage_report_file_path = os.path.join(stu_folder, 'pytest_coverage_report.json')
    pytest_report_path = os.path.join(stu_folder, 'pytest_report.json')

    command = [
        'pytest', '--no-header','--tb=line', '--timeout=5', '--timeout_method=signal',
        '--json-report', f'--json-report-file={pytest_report_path}', test_suite_stu_path
    ]
    
    if ON_HEROKU:
        subprocess.run(command, check=False)
    else:
        with open(test_results_file_path, 'w') as f:
            subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, check=False)

    if check_passed_all_tests(pytest_report_path):
    # and get_coverage(pytest_coverage_report_file_path)>=STU_COVERAGE_THRESHOLD:
        return True
    else:
        return False
        

def test_simulated_students(task_path, task):
    num_stu_passed = 0
    task_folder = os.path.join('/app', task_path, task) if ON_HEROKU else os.path.join(task_path, task)
    students_folder = os.path.join(task_folder, 'simulated_students')
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for stu in os.listdir(students_folder):
            future = executor.submit(test_student, os.path.join(students_folder, stu), task_folder)
            futures.append(future)
        
        for future in as_completed(futures):
            if future.result():
                num_stu_passed += 1
    print("num_stu_passed=", num_stu_passed)
    if num_stu_passed/STU_POPULATION_SIZE*100 >= STU_POPULATION_PASSING_THRESHOLD:
        return True
    else:
        return False

def test_ta(ta_testsuite_folder, task_folder):
    # list all files in ta_testsuite_folder
    files = os.listdir(ta_testsuite_folder)
    print('files:', files)
    
    test_suite_ta_path = os.path.join(ta_testsuite_folder, 'test_suite_ta.py')
    task_suite_path = os.path.join(task_folder, 'test_suite.py')
    
    with open(task_suite_path, 'r') as f:
        test_suite_content = f.read().replace('from solution import', 'from program import').replace('from solution_program import', 'from program import')
        # test_suite_content = test_suite_content
    
    with open(test_suite_ta_path, 'w') as f:
        f.write("from program import *\n" + test_suite_content)

    test_results_file_path = os.path.join(ta_testsuite_folder, 'test_results.txt')
    pytest_coverage_report_file_path = os.path.join(ta_testsuite_folder, 'pytest_coverage_report.json')
    pytest_report_path = os.path.join(ta_testsuite_folder, 'pytest_report.json')

    command = [
        'pytest', '--tb=line','--timeout=5', '--timeout_method=signal',
        f'--cov=program', f'--cov-report=json:{pytest_coverage_report_file_path}',
        '--json-report', f'--json-report-file={pytest_report_path}', test_suite_ta_path
    ]

    if ON_HEROKU:
        subprocess.run(command, check=False)
    else:
        with open(test_results_file_path, 'w') as f:
            subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, check=False)

    if check_passed_all_tests(pytest_report_path) and get_coverage(pytest_coverage_report_file_path) >= TUTOR_TESTSUITE_COVERAGE_THRESHOLD:
        return True
    else:
        return False


def test_ta_testsuite(task_path, task):
    task_folder = os.path.join('/app', task_path, task) if ON_HEROKU else os.path.join(task_path, task)
    # os.makedirs(task_folder, exist_ok=True)
    ta_testsuite_folder = os.path.join(task_folder, 'simulated_tutors')
    
    high_quality_testsuite = True
    for ta in os.listdir(ta_testsuite_folder):
        if not test_ta(os.path.join(ta_testsuite_folder, ta), task_folder):
            high_quality_testsuite = False
            break
    
    return high_quality_testsuite
    

def compute_simulated_distribution(query_path, num_tasks_per_pair):
    results_path = os.path.join(query_path, 'results.csv')
    results = pd.read_csv(results_path)
    tasks = sorted(results['task'].unique(), key=lambda x: int(x.split('_')[1]))

    pd_data = pd.DataFrame({
        'task': tasks,
        'gen_consistency': results['gen_consistency'],
        'q_testsuite': results['Q-Testsuite'],
        'llm_judge': results['LLMJudge'],
        'q_context': results['Q-Context'],
        'num_passed_stu': results['num_passed_stu'],
        'perc_passed_stu': np.where(results['total_num_stu'] != 0, results['num_passed_stu'] / results['total_num_stu'] * 100, 0)
    })

    print('pd_data:', pd_data)

    summary_dict = {}
    list_N = [1] + list(range(5, num_tasks_per_pair + 1, 5))
    for N in list_N:
        filtered_pd_data = pd_data.sample(n=N, random_state=208).sort_values(by='task', key=lambda x: x.str.split('_').str[1].astype(int))
        passed_tasks = {
            'Base': filtered_pd_data['task'].tolist(),
            'GenConsistency': filtered_pd_data[(filtered_pd_data['gen_consistency']==1)]['task'].tolist(),
            'LLMJudge': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['llm_judge'] == 1)]['task'].tolist(),
            # 'ValTests': filtered_pd_data[filtered_pd_data['q_testsuite'] == 1.0]['task'].tolist(),
            'SimTutorsVal': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0)]['task'].tolist(),
            'SimStudentsVal-0%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 0) ]['task'].tolist(),
            'SimStudentsVal-5%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 5) ]['task'].tolist(),
            'SimStudentsVal-10%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 10) ]['task'].tolist(),
            'SimStudentsVal-15%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 15) ]['task'].tolist(),
            'SimStudentsVal-20%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 20) ]['task'].tolist(),
            'SimStudentsVal-25%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 25) ]['task'].tolist(),
            'SimStudentsVal-30%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 30) ]['task'].tolist(),
            'SimStudentsVal-35%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 35) ]['task'].tolist(),
            'SimStudentsVal-40%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 40) ]['task'].tolist(),
            'SimStudentsVal-45%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 45) ]['task'].tolist(),
            'SimStudentsVal-50%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 50) ]['task'].tolist(),
            'SimStudentsVal-55%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 55) ]['task'].tolist(),
            'SimStudentsVal-60%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 60) ]['task'].tolist(),
            'SimStudentsVal-65%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 65) ]['task'].tolist(),
            'SimStudentsVal-70%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 70) ]['task'].tolist(),
            'SimStudentsVal-75%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 75) ]['task'].tolist(),
            'SimStudentsVal-80%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 80) ]['task'].tolist(),
            'SimStudentsVal-85%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 85) ]['task'].tolist(),
            'SimStudentsVal-90%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 90) ]['task'].tolist(),
            'SimStudentsVal-95%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 95) ]['task'].tolist(),
            'SimStudentsVal-100%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['perc_passed_stu'] >= 100) ]['task'].tolist(),
            
            'PyTaskSyn-0%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 0)]['task'].tolist(),
            'PyTaskSyn-5%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 5)]['task'].tolist(),
            'PyTaskSyn-10%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 10)]['task'].tolist(),
            'PyTaskSyn-15%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 15)]['task'].tolist(),
            'PyTaskSyn-20%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 20)]['task'].tolist(),
            'PyTaskSyn-25%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 25)]['task'].tolist(),
            'PyTaskSyn-30%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 30)]['task'].tolist(),
            'PyTaskSyn-35%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 35)]['task'].tolist(),
            'PyTaskSyn-40%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 40)]['task'].tolist(),
            'PyTaskSyn-45%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 45)]['task'].tolist(),
            'PyTaskSyn-50%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 50)]['task'].tolist(),
            'PyTaskSyn-55%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 55)]['task'].tolist(),
            'PyTaskSyn-60%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 60)]['task'].tolist(),
            'PyTaskSyn-65%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 65)]['task'].tolist(),
            'PyTaskSyn-70%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 70)]['task'].tolist(),
            'PyTaskSyn-75%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 75)]['task'].tolist(),
            'PyTaskSyn-80%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 80)]['task'].tolist(),
            'PyTaskSyn-85%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 85)]['task'].tolist(),
            'PyTaskSyn-90%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 90)]['task'].tolist(),
            'PyTaskSyn-95%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) & (filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 95)]['task'].tolist(),
            'PyTaskSyn-100%': filtered_pd_data[(filtered_pd_data['gen_consistency']==1) &(filtered_pd_data['q_testsuite'] == 1.0) & (filtered_pd_data['q_context'] == 1.0) & (filtered_pd_data['perc_passed_stu'] >= 100)]['task'].tolist()
        }
        summary_dict[N] = passed_tasks

    with open(os.path.join(query_path, 'passed_tasks_for_each_technique.json'), 'w') as f:
        json.dump(summary_dict, f)

    return summary_dict

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_tasks', type=int, default=5, help='Number of tasks')
    parser.add_argument('--task_path', type=str, default='outputs/tasks', help='Output path')

    args = parser.parse_args()

    test_simulated_students(args.task_path, 'task_0')
