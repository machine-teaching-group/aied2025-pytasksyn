from .utils import check_passed_all_tests, get_coverage
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import multiprocessing
import subprocess

MAX_WORKERS = max(4, multiprocessing.cpu_count() - 1)

def run_pytest(task_path, test_solution_results_file_path):
    pytest_coverage_report_file_path = os.path.join(task_path, 'pytest_coverage_report.json')
    pytest_report_path = os.path.join(task_path, 'pytest_report.json')
    test_suite_sol_path = os.path.join(task_path, 'test_suite_sol.py')
    
    cmd = [
        'pytest',
        '--no-header',
        '--quiet',
        '--tb=line',
        '--timeout=5',
        '--timeout_method=signal',
        # f'--cov=solution_program',
        # f'--cov-report=json:{pytest_coverage_report_file_path}',
        '--json-report',
        f'--json-report-file={pytest_report_path}',
        test_suite_sol_path
    ]
    
    with open(test_solution_results_file_path, 'w') as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=False)

def prepare_test_suite(task_path):
    test_suite_sol_path = os.path.join(task_path, 'test_suite_sol.py')
    test_suite_path = os.path.join(task_path, 'test_suite.py')
    
    with open(test_suite_path, 'r') as f_in, open(test_suite_sol_path, 'w') as f_out:
        f_out.write("from solution_program import *\n")
        for line in f_in:
            f_out.write(line.replace('from solution import', 'from solution_program import'))
    
    return test_suite_sol_path

def check_gen_consistency(task_path):
    try:
        prepare_test_suite(task_path)
        test_solution_results_file_path = os.path.join(task_path, 'test_solution_results.txt')
        run_pytest(task_path, test_solution_results_file_path)
        return check_passed_all_tests(os.path.join(task_path, 'pytest_report.json'))
    except Exception as e:
        print(f"Failed to test solution for task {task_path}: {e}")
        return 0