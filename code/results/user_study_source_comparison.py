import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
# use tex fonts
plt.rcParams['text.usetex'] = True

expert = {"theme": 0.0, "concepts": 0.0, "difficulty": 0.0, "interestingness": 0.0, "participant_success": 0.0, "avg_participant_time_to_solve": 0.0}
geeksforgeeks = {"theme": 0.0, "concepts": 0.0, "difficulty": 0.0, "interestingness": 0.0, "participant_success": 0.0, "avg_participant_time_to_solve": 0.0}
pytasksyn = {"theme": 0.0, "concepts": 0.0, "difficulty": 0.0, "interestingness": 0.0, "participant_success": 0.0, "avg_participant_time_to_solve": 0.0}

study_tasks_df = pd.read_csv("./outputs/user_study_source_comparison/study_tasks.csv", delimiter=",")
geeksforgeeks_tasks = list(study_tasks_df[study_tasks_df['source'] == 'geeksforgeeks']['task_id'])
pytasksyn_tasks = list(study_tasks_df[study_tasks_df['source'] == 'pytasksyn']['task_id'])
expert_tasks = list(study_tasks_df[study_tasks_df['source'] == 'expert']['task_id'])

data_path = "./outputs/user_study_source_comparison/"
studentattempt_df = pd.read_csv(data_path + 'pytask_api_studentattempt.csv')
problemfeedback_df = pd.read_csv(data_path + 'pytask_api_problemfeedback.csv')
problemfeedback_df['q-context'] = (problemfeedback_df['context_satisfaction'] == 1) & (problemfeedback_df['concepts_satisfaction'] == 1)

# Participant IDs and problem IDs
UIDS = [13, 14, 16, 18, 35, 37, 38, 67, 102, 135]
PIDS = [i for i in range(1045, 1060)]
problemfeedback_df = problemfeedback_df[problemfeedback_df['comments'] != 'FOR DEBUGGING & TESTING']
problemfeedback_df = problemfeedback_df[problemfeedback_df['user_id'].isin(UIDS)]
problemfeedback_df = problemfeedback_df[problemfeedback_df['problem_id'].isin(PIDS)]
problemfeedback_df = problemfeedback_df.sort_values(by='created_at', ascending=True)

# compute average interestingness
avg_interestingness = problemfeedback_df['interestingness'].mean()

# compute average difficulty
avg_difficulty = problemfeedback_df['difficulty'].mean()
total_difficulty = len(problemfeedback_df)
num_hard = len(problemfeedback_df[problemfeedback_df['difficulty'] == 1])
num_medium = len(problemfeedback_df[problemfeedback_df['difficulty'] == 0.5])
num_easy = len(problemfeedback_df[problemfeedback_df['difficulty'] == 0])
print('% problems with difficulty rating of 1 "hard": ', round(num_hard / total_difficulty * 100, 1))
print('% problems with difficulty rating of 0.5 "medium": ', round(num_medium / total_difficulty * 100, 1))
print('% problems with difficulty rating of 0 "easy": ', round(num_easy / total_difficulty * 100, 1))

# Calculate percentage of problems with different interestingness ratings
total_interestingness = len(problemfeedback_df)
num_interesting = len(problemfeedback_df[problemfeedback_df['interestingness'] == 1])
num_okay = len(problemfeedback_df[problemfeedback_df['interestingness'] == 0.5])
num_boring = len(problemfeedback_df[problemfeedback_df['interestingness'] == 0])
print('% problems with interestingness rating of 1 "interesting": ', round(num_interesting / total_interestingness * 100, 1))
print('% problems with interestingness rating of 0.5 "okay": ', round(num_okay / total_interestingness * 100, 1))
print('% problems with interestingness rating of 0 "boring": ', round(num_boring / total_interestingness * 100, 1))
print('========================================\n')

# compute theme_satisfaction for expert, geeksforgeeks, pytasksyn tasks
expert_tasks_theme_satisfaction = problemfeedback_df[problemfeedback_df['problem_id'].isin(expert_tasks)]['context_satisfaction'].mean()
geeksforgeeks_tasks_theme_satisfaction = problemfeedback_df[problemfeedback_df['problem_id'].isin(geeksforgeeks_tasks)]['context_satisfaction'].mean()
pytasksyn_tasks_theme_satisfaction = problemfeedback_df[problemfeedback_df['problem_id'].isin(pytasksyn_tasks)]['context_satisfaction'].mean()
print('expert_tasks_theme_satisfaction: ', round(expert_tasks_theme_satisfaction, 2))
print('pytasksyn_tasks_theme_satisfaction: ', round(pytasksyn_tasks_theme_satisfaction, 2))
print('geeksforgeeks_tasks_theme_satisfaction: ', round(geeksforgeeks_tasks_theme_satisfaction, 2))
print('========================================\n')

# compute concepts_satisfaction for expert, geeksforgeeks, pytasksyn tasks
expert_tasks_concepts_satisfaction = problemfeedback_df[problemfeedback_df['problem_id'].isin(expert_tasks)]['concepts_satisfaction'].mean()
geeksforgeeks_tasks_concepts_satisfaction = problemfeedback_df[problemfeedback_df['problem_id'].isin(geeksforgeeks_tasks)]['concepts_satisfaction'].mean()
pytasksyn_tasks_concepts_satisfaction = problemfeedback_df[problemfeedback_df['problem_id'].isin(pytasksyn_tasks)]['concepts_satisfaction'].mean()
print('expert_tasks_concepts_satisfaction: ', round(expert_tasks_concepts_satisfaction, 2))
print('pytasksyn_tasks_concepts_satisfaction: ', round(pytasksyn_tasks_concepts_satisfaction, 2))
print('geeksforgeeks_tasks_concepts_satisfaction: ', round(geeksforgeeks_tasks_concepts_satisfaction, 2))
print('========================================\n')

# compute q-context for expert, geeksforgeeks, pytasksyn tasks
expert_tasks_q_context = problemfeedback_df[problemfeedback_df['problem_id'].isin(expert_tasks)]['q-context'].mean()
geeksforgeeks_tasks_q_context = problemfeedback_df[problemfeedback_df['problem_id'].isin(geeksforgeeks_tasks)]['q-context'].mean()
pytasksyn_tasks_q_context = problemfeedback_df[problemfeedback_df['problem_id'].isin(pytasksyn_tasks)]['q-context'].mean()
print('expert_tasks_q_context: ', round(expert_tasks_q_context, 2))
print('pytasksyn_tasks_q_context: ', round(pytasksyn_tasks_q_context, 2))
print('geeksforgeeks_tasks_q_context: ', round(geeksforgeeks_tasks_q_context, 2))
print('========================================\n')

# compute comprehensible score for expert, geeksforgeeks, pytasksyn tasks
expert_tasks_comprehensible = problemfeedback_df[problemfeedback_df['problem_id'].isin(expert_tasks)]['comprehensible'].mean()
geeksforgeeks_tasks_comprehensible = problemfeedback_df[problemfeedback_df['problem_id'].isin(geeksforgeeks_tasks)]['comprehensible'].mean()
pytasksyn_tasks_comprehensible = problemfeedback_df[problemfeedback_df['problem_id'].isin(pytasksyn_tasks)]['comprehensible'].mean()
print('expert_tasks_comprehensible: ', round(expert_tasks_comprehensible, 2))
print('pytasksyn_tasks_comprehensible: ', round(pytasksyn_tasks_comprehensible, 2))
print('geeksforgeeks_tasks_comprehensible: ', round(geeksforgeeks_tasks_comprehensible, 2))

time_taken_dict = {'expert': [], 'geeksforgeeks': [], 'pytasksyn': []}
solved_dict = {'expert': [], 'geeksforgeeks': [], 'pytasksyn': []}

for pid in PIDS:
    # get source of pid from study_tasks_df
    source = study_tasks_df[study_tasks_df['task_id'] == pid]['source'].iloc[0]
    for uid in UIDS:
        # get the attempts of pid by uid
        attempts = studentattempt_df[(studentattempt_df['problem_id'] == pid) & (studentattempt_df['user_id'] == uid)]
        if len(attempts) == 0:
            continue
        # get the first attempt
        first_attempt = attempts.sort_values(by='created_at', ascending=True).iloc[0]
        # get the last attempt
        last_attempt = attempts.sort_values(by='created_at', ascending=False).iloc[0]
        # get the time taken
        finished_at = datetime.strptime(last_attempt['created_at'].split(' +')[0], '%Y-%m-%d %H:%M:%S.%f')
        started_at = datetime.strptime(first_attempt['created_at'].split(' +')[0], '%Y-%m-%d %H:%M:%S.%f')
        time_taken = finished_at - started_at
        # convert to seconds
        time_taken = time_taken.total_seconds()
        test_results = last_attempt['test_results']
        # convert to json
        test_results_json = json.loads(test_results)
        if 'summary' in test_results_json:
            if 'passed' in test_results_json['summary']:
                if test_results_json['summary']['passed'] == test_results_json['summary']['total']:
                    solved_dict[source].append(1)
                else:
                    solved_dict[source].append(0)
        else:
            solved_dict[source].append(0)

        if time_taken > 1200:
            print("pid: ", pid, " uid: ", uid, " time_taken: ", time_taken)
            print(first_attempt['created_at'])
            print(last_attempt['created_at'])
            print("started_at: ", started_at)
            print("finished_at: ", finished_at)
        
        time_taken_dict[source].append(time_taken)

print(solved_dict)
print(time_taken_dict)

for source in ['expert', 'geeksforgeeks', 'pytasksyn']:
    print("average time taken to solve a problem for ", source, ": ", round(sum(time_taken_dict[source]) / len(time_taken_dict[source]) / 60, 2), " minutes")
    print("average solved rate for ", source, ": ", round(sum(solved_dict[source]) / len(solved_dict[source]), 2))

# Get unique sources from study_tasks_df
sources = study_tasks_df['source'].unique()
difficulty_means = {}
interestingness_means = {}

for source in sources:
    source_pids = study_tasks_df[study_tasks_df['source'] == source]['task_id']
    source_problems = problemfeedback_df[problemfeedback_df['problem_id'].isin(source_pids)]

    difficulty_mean = source_problems['difficulty'].mean()
    difficulty_means[source] = difficulty_mean
    
    interestingness_mean = source_problems['interestingness'].mean()
    interestingness_means[source] = interestingness_mean

print("Mean difficulty by source:")
for source, mean in difficulty_means.items():
    print(f"{source}: {mean:.2f}")

print("\nMean interestingness by source:")
for source, mean in interestingness_means.items():
    print(f"{source}: {mean:.2f}")





    
