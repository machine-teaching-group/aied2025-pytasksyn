import os
import json
import time

path = 'experiments_20240816'
gpt4o_mini_input_token_cost = 0.15/1e6 # per 1M
gpt4o_mini_output_token_cost = 0.6/1e6 # per 1M
gpt4o_input_token_cost = 2.5/1e6 # per 1M
gpt4o_output_token_cost = 10/1e6 # per 1M

tasks_generation_cost = []
teaching_assistant_simulation_cost = []
student_simulation_cost = []

queries = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder))]
for query in queries:
    query_path = os.path.join(path, query)
    # load token_count.json
    with open(os.path.join(path, query, 'token_count.json'), 'r') as f:
        query_token_count = json.load(f)
    tasks_generation_cost.append(query_token_count['prompt_tokens'] * gpt4o_input_token_cost + query_token_count['completion_tokens'] * gpt4o_output_token_cost)

    tasks = [folder for folder in os.listdir(query_path) if os.path.isdir(os.path.join(query_path, folder))]

    ta_cost = 0
    student_cost = 0
    for task in tasks:
        task_path = os.path.join(query_path, task)
        if os.path.exists(os.path.join(task_path, 'token_count.json')):
        # load token_count.json
            with open(os.path.join(task_path, 'token_count.json'), 'r') as f:
                task_token_count = json.load(f)
                ta_cost += task_token_count["teaching_assistant"]["prompt_tokens"] * gpt4o_mini_input_token_cost + task_token_count["teaching_assistant"]["completion_tokens"] * gpt4o_mini_output_token_cost
                student_cost += task_token_count["student"]["prompt_tokens"] * gpt4o_mini_input_token_cost + task_token_count["student"]["completion_tokens"] * gpt4o_mini_output_token_cost
    teaching_assistant_simulation_cost.append(ta_cost)
    student_simulation_cost.append(student_cost)

print("--Tasks generation cost per query: ", sum(tasks_generation_cost)/len(tasks_generation_cost))
print("--Teaching assistant simulation cost per query: ", sum(teaching_assistant_simulation_cost) / len(teaching_assistant_simulation_cost))
print("--Student simulation cost per query: ", sum(student_simulation_cost)/len(student_simulation_cost))