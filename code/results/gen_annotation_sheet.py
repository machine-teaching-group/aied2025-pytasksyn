import os
import pandas as pd
import json
import argparse
from code.utils import check_passed_all_tests, get_coverage, get_perc_passed_tests
if __name__ == '__main__':
    #parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str, required=True, help='path to the experiment')
    args = parser.parse_args()
    output_path = args.output_path

    pd_data = pd.DataFrame(columns=['query', 'theme', 'programming_concepts', 'task', 'self_consistency', 'Q-TestSuite', 'Q-Context',
                                    'Q-Comprehensive', 'Q-Overall', 'contain_higher_level_concepts'])
    sorted_queries = [folder for folder in os.listdir(output_path) if os.path.isdir(os.path.join(output_path, folder))]
    sorted_queries.sort(key = lambda x: int(x.split('_')[1]))
    for query in sorted_queries:
        query_path = os.path.join(output_path, query)
        if not os.path.isdir(query_path):
            continue
        with open(os.path.join(query_path, 'theme.txt'), 'r') as f:
            theme = f.read()
        with open(os.path.join(query_path, 'programming_concepts.txt'), 'r') as f:
            programming_concepts = f.read()
        sorted_tasks = [folder for folder in os.listdir(query_path) if os.path.isdir(os.path.join(query_path, folder))]
        sorted_tasks.sort(key = lambda x: int(x.split('_')[1]))
        for task in sorted_tasks:
            task_path = os.path.join(query_path, task)
            if not os.path.isdir(task_path):
                continue
            print('task_path', task_path)
            passed_all_tests = round(get_perc_passed_tests(os.path.join(task_path, 'pytest_report.json')),2)
            coverage = round(get_coverage(os.path.join(task_path, 'pytest_coverage_report.json')),2)
            pd_data = pd.concat([pd_data, pd.DataFrame({'query': query, 'theme': theme, 'programming_concepts': programming_concepts, 'task': task, 'self_consistency': 1 if passed_all_tests==100.0 else 0}, index=[0])], ignore_index=True)
                                                        
    pd_data.to_csv(os.path.join(output_path, 'annotation_sheet.csv'), index=False)

    
# Commands to clean up the folder
# find . -type d -name "__pycache__" -exec rm -r {} +
# find . -type d -name ".pytest_cache" -exec rm -r {} +
# find . -type d -name "simulated_students" -exec rm -r {} +
# find . -type d -name "simulated_tutors" -exec rm -r {} +
# find . -type f -name ".coverage" -exec rm -f {} +
# find . -type f -name "test_matrix.csv" -exec rm -f {} +
# find . -type f -name "test_matrix.pdf" -exec rm -f {} +
# find . -type f -name "test_solution_results.txt" -exec rm -f {} +
# find . -type f -name "test_suite_sol.py" -exec rm -f {} +
# find . -type f -name "prompt.txt" -exec rm -f {} +
# find . -type f -name "responses.json" -exec rm -f {} +
# find . -type f -name "results.csv" -exec rm -f {} +
# find . -type f -name "token_count.json" -exec rm -f {} +
# find . -type f -name "pytest_report.json" -exec rm -f {} +
# find . -type f -name "pytest_coverage_report.json" -exec rm -f {} +
# find . -type f -name "execution_time.txt" -exec rm -f {} +
# find . -type f -name "passed_1st_validation_tasks.txt" -exec rm -f {} +
# find . -type f -name "passed_tasks_for_each_technique.json" -exec rm -f {} +
# find . -type f -name "responses.txt" -exec rm -f {} +
# find . -type f -name "context.txt" -exec rm -f {} +
# find . -type f -name "programming_concepts.txt" -exec rm -f {} +
# find . -type d -name "simulated_tutors_testsuite" -exec rm -r {} +
# find . -type d -name "simulated_judges" -exec rm -r {} +
