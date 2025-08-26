import os

import json
import argparse
from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from .query_agents import query_simulated_students, parse_simulated_students_responses, query_simulated_tutor, query_simulated_judge
from .run_test import test_simulated_students, compute_simulated_distribution, test_ta_testsuite
from .analyze import analyze_results
import random
from .utils import check_passed_all_tests, get_coverage
from .task_generation import gen_tasks, parse_task
from .gen_consistency import check_gen_consistency
from time import sleep
import logging
random.seed(1)

# Get the directory of the current script
script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
ON_HEROKU = eval(os.environ.get("ON_HEROKU"))
if ON_HEROKU:
    from ..data.prompt_templates import *
    MAX_WORKERS = 20
else:
    from data.prompt_templates import *
    MAX_WORKERS = 10

def get_task(path_to_selected_task):
    with open(os.path.join(path_to_selected_task, 'task_description.txt'), 'r') as f:
        task_description = f.read()
    with open(os.path.join(path_to_selected_task, 'solution_program.py'), 'r') as f:
        solution_code = f.read()
    with open(os.path.join(path_to_selected_task, 'test_suite.py'), 'r') as f:
        test_driver = f.read()
    return task_description, solution_code, test_driver

def validate_query(theme, programming_concepts, query_path, model_configuration, task_responses, num_tasks_per_pair):
    student_population_passing_threshold = model_configuration['student']['population_passing_threshold']

    task_dict = {}

    for i in range(num_tasks_per_pair):
        task = f'task_{i}'
        task_path = os.path.join(query_path, task)
        task, task_description, solution_program, test_suite = parse_task(i, task_responses[i], query_path, theme, programming_concepts)
        task_dict[task] = {
            'task_description': task_description,
            'solution_program': solution_program,
            'test_suite': test_suite
        }
        if not ON_HEROKU:
            query_simulated_judge(query_path, theme, programming_concepts, task, model_configuration, task_dict)
        gen_consistency = check_gen_consistency(task_path)
        if not ON_HEROKU or gen_consistency:
            context_satisfied = query_simulated_tutor(query_path, theme, programming_concepts, task, model_configuration, task_dict)
            print('context_satisfied:', context_satisfied)
            if not ON_HEROKU or context_satisfied:                
                high_quality_testsuite = test_ta_testsuite(query_path, task)
                print('high_quality_testsuite:', high_quality_testsuite)
                if not ON_HEROKU or high_quality_testsuite:
                    query_simulated_students(query_path, task, model_configuration, task_dict)
                    print('test_simulated_students:', test_simulated_students(query_path, task))
                    if test_simulated_students(query_path, task) and ON_HEROKU:
                        print('task_dict[task]:', task_dict[task])
                        return task_dict[task]['task_description'], task_dict[task]['solution_program'], task_dict[task]['test_suite']
    return None, None, None

def generate_task(query=None, theme=None, programming_concepts=None, model_configuration=None, num_tasks_per_pair=10, output_path='outputs'):
    start = time.time()
    if model_configuration==None:
        with open(os.path.join(parent_dir, 'data', 'model_configuration.json'), 'r') as f:
            model_configuration = json.load(f)
    
    if query!=None:
        query_path = os.path.join(output_path, query)
    else:
        datetimestr = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_path = os.path.join(output_path, datetimestr)

    os.makedirs(query_path, exist_ok=True)
    print('query_path:', query_path)

    if not ON_HEROKU:
        ### Write theme and programming_concepts to files
        with open(os.path.join(query_path, 'theme.txt'), 'w') as f:
            f.write(theme)
        with open(os.path.join(query_path, 'programming_concepts.txt'), 'w') as f:
            f.write(str(programming_concepts))

    ### Generate a pool of tasks
    task_responses = gen_tasks(query_path, theme, programming_concepts, num_tasks_per_pair, model_configuration)

    print('Successfully generated tasks')

    selected_task_description, selected_solution_program, selected_test_suite = validate_query(theme, programming_concepts, query_path, model_configuration, task_responses, num_tasks_per_pair)
    
    print("selected_task_description:", selected_task_description)
    print("selected_solution_program:", selected_solution_program)
    print("selected_test_suite:", selected_test_suite)

    if not ON_HEROKU:
        end = time.time()
        # save execution time to a file
        with open(os.path.join(query_path, 'execution_time.txt'), 'w') as f:
            f.write(str(end-start))

    if selected_task_description==None or selected_solution_program==None or selected_test_suite==None:
        print('No task passed validations')
        return None, None, None
    else:
        return selected_task_description, selected_solution_program, selected_test_suite

def sample(themes, programming_concepts, num_themes, num_num_concept_lists_per_theme):
    # sample 5 themes uniformly at random
    n_themes = num_themes
    n_list_concepts_per_theme = num_num_concept_lists_per_theme
    sampled_themes = random.sample(themes, n_themes)
    sampled = []
    # sample 3-5 programming concepts uniformly at random
    for i in range(n_themes):
        for j in range(n_list_concepts_per_theme):
            theme = sampled_themes[i]
            num_concepts = random.randint(3,5)
            sampled_concepts = random.sample(programming_concepts, num_concepts)
            sampled.append({'theme': theme, 'concepts': sampled_concepts})
    # save the sampled themes and programming concepts to a file
    with open(os.path.join(parent_dir, 'data', 'sampled_themes_and_concepts.json'), 'w') as f:
        json.dump(sampled, f)
    
    return sampled
    
if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Generate tasks for students')
    parser.add_argument('--num_themes', type=int, default=5)  
    parser.add_argument('--num_concept_lists_per_theme', type=int, default=1)  
    parser.add_argument('--num_tasks_per_pair', type=int, default=10)
    parser.add_argument('--output_path', type=str, default='outputs')
    
    #example command: python -m code.main --num_themes 5 --num_concept_lists_per_theme 1 --num_tasks_per_pair 10 --output_path outputs
    args = parser.parse_args()

    with open(os.path.join(parent_dir, 'data', 'model_configuration.json'), 'r') as f:
        model_configuration = json.load(f)

    # Load themes_and_concepts.json
    with open('data/themes_and_concepts.json', 'r') as f:
        themes_and_concepts = json.load(f)
        themes = themes_and_concepts['themes']
        programming_concepts = themes_and_concepts['concepts']
    
    sampled = sample(themes, programming_concepts, args.num_themes, args.num_concept_lists_per_theme)

    for query in range(len(sampled)):
        sampled_pair = sampled[query]
        theme = sampled_pair['theme']
        programming_concepts = sampled_pair['concepts']
        selected_task_description, selected_solution_program, selected_test_suite = generate_task('query_' + str(query), theme, programming_concepts, model_configuration, args.num_tasks_per_pair, args.output_path)
        query_path = os.path.join(args.output_path, 'query_' + str(query))
        analyze_results(query_path)
        summary_dict = compute_simulated_distribution(query_path, args.num_tasks_per_pair)