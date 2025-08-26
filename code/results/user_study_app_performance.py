import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
# use tex fonts
plt.rcParams['text.usetex'] = True

data_path = "outputs/user_study_app_performance/"
# Load the data from CSV files
customuser_df = pd.read_csv(data_path + 'pytask_api_customuser.csv')
problem_df = pd.read_csv(data_path + 'pytask_api_problem.csv')
problemrequest_df = pd.read_csv(data_path + 'pytask_api_problemrequest.csv')
studentattempt_df = pd.read_csv(data_path + 'pytask_api_studentattempt.csv')
problemfeedback_df = pd.read_csv(data_path + 'pytask_api_problemfeedback.csv')

# filter problemfeedback_df rows with comment 'FOR DEBUGGING & TESTING'
problemfeedback_df = problemfeedback_df[problemfeedback_df['comments'] != 'FOR DEBUGGING & TESTING']
# filter problemfeedback_df rows with user_id not in customuser_df
problemfeedback_df = problemfeedback_df[problemfeedback_df['user_id'].isin(customuser_df['id'])]
# in problemfeedback_df, if found feedback with the same user_id and problem_id, remove the one with the lowest created_at
problemfeedback_df = problemfeedback_df.sort_values(by='created_at', ascending=True)
problemfeedback_df = problemfeedback_df.drop_duplicates(subset=['user_id', 'problem_id'], keep='first')
problemfeedback_df = problemfeedback_df.groupby('user_id').head(5)

# filter problemrequest_df rows with user_id not in customuser_df
problemrequest_df = problemrequest_df[problemrequest_df['user_id'].isin(customuser_df['id'])]

#== Compute coverage by counting the number problem requests that have a problem_id (not null)
coverage = problemrequest_df['problem_id'].notna().sum()/len(problemrequest_df)
print("coverage rate: ", round(coverage*100, 1) )

# count the number of problem requests per user
problemrequest_df['num_problem_requests'] = problemrequest_df.groupby('user_id')['user_id'].transform('count')
print("num_problem_requests=", problemrequest_df['num_problem_requests'].unique())
num_problem_requests_dict = problemrequest_df.groupby('user_id')['num_problem_requests'].first().to_dict()
# sort num_problem_requests_dict by user_id
num_problem_requests_dict = dict(sorted(num_problem_requests_dict.items(), key=lambda item: item[0]))
print("num_problem_requests_dict=", num_problem_requests_dict)
# compute mean and std of num_problem_requests
mean_num_problem_requests = sum(num_problem_requests_dict.values()) / len(num_problem_requests_dict)
std_num_problem_requests = np.std(list(num_problem_requests_dict.values()))/np.sqrt(len(num_problem_requests_dict))
print("mean_num_problem_requests=", round(mean_num_problem_requests, 2))
print("std_num_problem_requests=", round(std_num_problem_requests, 2))

# filter out problemfeedback_df rows with no problem_id
problemrequest_df = problemrequest_df[problemrequest_df['problem_id'].notna()]
# if any user has more than 5 problem requests, get the first 5
problemrequest_df = problemrequest_df.groupby('user_id').head(5)
print("len(problemrequest_df)=", len(problemrequest_df))

concepts_counts = {}
for index, row in problemrequest_df.iterrows():
    programming_concepts = row['programming_concepts']
    programming_concepts = programming_concepts.split(',')
    for concept in programming_concepts:
        if 'etc.)' in concept or 'if/else' in concept:
            concept = 'Selection Statements'
        concept = concept.strip()
        if concept not in concepts_counts:
            concepts_counts[concept] = 0
        concepts_counts[concept] += 1
print("concepts_counts=", concepts_counts)

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

# compute average comprehensible
avg_comprehensible = problemfeedback_df['comprehensible'].mean()
print('avg Q-comprehensible: ', round(avg_comprehensible, 2))

# compute average concepts_satisfaction
avg_concepts_satisfaction = problemfeedback_df['concepts_satisfaction'].mean()
print('avg Q-Concepts satisfaction: ', round(avg_concepts_satisfaction, 2))

# compute average context_satisfaction
avg_context_satisfaction = problemfeedback_df['context_satisfaction'].mean()
print('avg Q-Theme satisfaction: ', round(avg_context_satisfaction, 2))

time_takes = []
user_stats = {}
for _, easy_problem in problemfeedback_df.iterrows():
    # find all student_attempt that solved the problem
    problem_id = easy_problem['problem_id']
    user_id = easy_problem['user_id']
    if user_id not in user_stats:
        user_stats[user_id] = {'num_problems_generated': 0, 'num_problems_solved': 0, 'time_taken': []}
    
    user_stats[user_id]['num_problems_generated'] += 1
    problem_created_at = problem_df.loc[problem_df['id'] == problem_id, 'created_at'].iloc[0]
    
    student_attempts = studentattempt_df[studentattempt_df['problem_id'] == problem_id]
    # get the last row by created_at
    last_student_attempt = student_attempts.sort_values(by='created_at', ascending=False).iloc[0]
    # get "test_results" column
    test_results = last_student_attempt['test_results']
    # convert to json
    test_results_json = json.loads(test_results)

    if 'summary' in test_results_json:
        if 'passed' in test_results_json['summary']:
            if test_results_json['summary']['passed'] == test_results_json['summary']['total']:
                finished_at = datetime.strptime(last_student_attempt['created_at'].split(' +')[0], '%Y-%m-%d %H:%M:%S.%f')
                problem_created_at = datetime.strptime(problem_created_at.split(' +')[0], '%Y-%m-%d %H:%M:%S.%f')
                time_taken = finished_at - problem_created_at
                # conver to seconds
                time_taken = time_taken.total_seconds()

                time_takes.append(time_taken)
                user_stats[user_id]['time_taken'].append(time_taken)
                user_stats[user_id]['num_problems_solved'] += 1

# average time taken in minutes
avg_time_taken = sum(time_takes) / len(time_takes) / 60
success_rate = len(time_takes) / len(problemfeedback_df)
print("solving success rate:", round(success_rate*100, 2), "%")
print("avg_time_taken_to_solv in minutes:", round(avg_time_taken, 2))

# Calculate frequency of each theme, difficulty, and interestingness
theme_counts = problemrequest_df['context'].value_counts()
difficulty_counts = problemfeedback_df['difficulty'].value_counts().sort_index()
difficulty_counts = difficulty_counts / len(problemfeedback_df) * 100
print(difficulty_counts)
difficulty_counts.index = difficulty_counts.index.map({0: 'easy', 0.5: 'medium', 1: 'hard'})
interestingness_counts = problemfeedback_df['interestingness'].value_counts().sort_index()
interestingness_counts = interestingness_counts / len(problemfeedback_df) * 100
interestingness_counts.index = interestingness_counts.index.map({0: 'boring', 0.5: 'okay', 1: 'interesting'})
interestingness_counts = interestingness_counts.sort_values(ascending=False)
print(interestingness_counts)


fig = plt.figure(figsize=(50, 4))
gs = fig.add_gridspec(1, 4, width_ratios=[1.2, 2.1, 0.6, 0.7], wspace=0.15)
# Set consistent font sizes
TITLE_SIZE = 60
LABEL_SIZE = 60
TICK_SIZE = 60
BAR_WIDTH = 0.6

# Plot 1: Theme counts
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor('#f8f8f8')  
themes = ["Science Fiction", "Cooking", "Game of Chance", 'Superheroes', "Board Games"]
themes_labels = ["Science\n fiction", "Cooking", "Game of\n Chance", 'Superheroes', "Board games"]
values = [theme_counts[theme]/len(problemfeedback_df)*100 for theme in themes]
rects1 = ax1.bar(themes, values, width=BAR_WIDTH, color='dodgerblue', alpha=0.95, edgecolor='black', linewidth=2)
ax1.set_ylabel('\% of tasks', fontsize=TITLE_SIZE)

ax1.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
ax1.set_xticklabels(themes_labels, fontsize=LABEL_SIZE, rotation=45)
ax1.grid(True, alpha=0.5)
ax1.set_yticks([0, 20, 40, 60, 80])
ax1.text(0.5, -1.5, '(a) Theme', transform=ax1.transAxes, fontsize=70, fontweight='bold', ha='center')

# Plot 2: Concepts counts
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor('#f8f8f8')  
concepts_items = sorted(concepts_counts.items(), key=lambda x: x[1], reverse=True)
concepts, counts = zip(*concepts_items)
concepts = ["Arithmetic Operators", "Variables", "Selection Statements", 'Loops', "Lists", 'Dictionaries', "Strings"]
# get the corresponding values from concepts_counts for each concept
values = [concepts_counts[concept] /len(problemfeedback_df)*100  for concept in concepts] 
rects2 = ax2.bar(concepts, values, width=BAR_WIDTH, color='dodgerblue', alpha=0.95, edgecolor='black', linewidth=2)
ax2.set_xticklabels(ax2.get_xticklabels(), fontsize=LABEL_SIZE)
ax2.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
concepts_labels = ["Arithmetic\n Operators", "Variables", "Selection\n Statements", 'Loops', "Lists", 'Dictionaries', "Strings"]
ax2.set_xticklabels(concepts_labels, fontsize=LABEL_SIZE, rotation=45)
ax2.grid(True, alpha=0.5)
ax2.set_yticks([0, 20, 40, 60, 80])
ax2.text(0.5, -1.5, '(b) Programming concepts', transform=ax2.transAxes, fontsize=70, fontweight='bold', ha='center')
ax2.set_xlim(-0.5, 6.5)

# Plot 2: Difficulty counts
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor('#f8f8f8')  
rects3 = ax3.bar(difficulty_counts.index, difficulty_counts.values, width=BAR_WIDTH, color='dodgerblue', alpha=0.95, edgecolor='black', linewidth=2)
ax3.set_xticklabels(ax3.get_xticklabels(), fontsize=LABEL_SIZE)
ax3.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
ax3.set_xticklabels(ax3.get_xticklabels(), fontsize=LABEL_SIZE, rotation=45)
ax3.grid(True, alpha=0.5)
ax3.set_yticks([0, 20, 40, 60, 80])
ax3.text(0.5, -1.5, '(c) Difficulty', transform=ax3.transAxes, fontsize=70, fontweight='bold', ha='center')

# Plot 3: Interestingness counts
ax4 = fig.add_subplot(gs[0, 3])
ax4.set_facecolor('#f8f8f8')  
interestingness_counts.index = interestingness_counts.index.map({'boring': 'Boring', 'okay': 'Okay', 'interesting': 'Interesting'})
interestingness_counts = interestingness_counts.reindex(['Interesting', 'Okay', 'Boring'])
rects4 = ax4.bar(interestingness_counts.index, interestingness_counts.values, width=BAR_WIDTH, color='dodgerblue', alpha=0.95, edgecolor='black', linewidth=2)
ax4.set_xticklabels(ax4.get_xticklabels(), fontsize=LABEL_SIZE)
ax4.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
ax4.set_xticklabels(ax4.get_xticklabels(), fontsize=LABEL_SIZE, rotation=45)
ax4.grid(True, alpha=0.5)
ax4.set_yticks([0, 20, 40, 60, 80])
ax4.text(0.5, -1.5, '(d) Interestingness', transform=ax4.transAxes, fontsize=70, fontweight='bold', ha='center')

# Adjust layout and save
plt.tight_layout()
plt.savefig('plots/theme_difficulty_interestingness_counts.pdf', bbox_inches='tight')
plt.close()

# compute the average time taken to solve a problem for each user
for user_id, stats in user_stats.items():
    avg_time_taken = round(sum(stats['time_taken']) / len(stats['time_taken']), 2) 
    avg_time_taken = round(avg_time_taken / 60, 2)
    user_stats[user_id]['avg_time_taken'] = avg_time_taken
    del user_stats[user_id]['time_taken']

# sort user_stats by user_id
user_stats = dict(sorted(user_stats.items(), key=lambda item: item[0]))
print("user_stats=", user_stats)


# compute average number of problems generated and solved and average time taken to solve a problem
avg_num_problems_generated = round(sum([stats['num_problems_generated'] for stats in user_stats.values()]) / len(user_stats), 2)
std_err_num_problems_generated = round(np.std([stats['num_problems_generated'] for stats in user_stats.values()]) / np.sqrt(len(user_stats)), 2)
avg_num_problems_solved = round(sum([stats['num_problems_solved'] for stats in user_stats.values()]) / len(user_stats), 2)
std_err_num_problems_solved = round(np.std([stats['num_problems_solved'] for stats in user_stats.values()]) / np.sqrt(len(user_stats)), 2)
avg_time_taken = round(sum([stats['avg_time_taken'] for stats in user_stats.values()]) / len(user_stats), 2)
std_err_time_taken = round(np.std([stats['avg_time_taken'] for stats in user_stats.values()]) / np.sqrt(len(user_stats)), 2)

print("avg_num_problems_generated=", avg_num_problems_generated)
print("std_err_num_problems_generated=", std_err_num_problems_generated)
print("avg_num_problems_solved=", avg_num_problems_solved)
print("std_err_num_problems_solved=", std_err_num_problems_solved)
print("avg_time_taken=", avg_time_taken)
print("std_err_time_taken=", std_err_time_taken)


generate_time_takes = []
for _, row in problemrequest_df.iterrows():
    problem_id = row['problem_id']
    problem_created_at = problem_df.loc[problem_df['id'] == problem_id, 'created_at'].iloc[0]
    request_created_at = datetime.strptime(row['created_at'].split(' +')[0], '%Y-%m-%d %H:%M:%S.%f')
    problem_created_at = datetime.strptime(problem_created_at.split(' +')[0], '%Y-%m-%d %H:%M:%S.%f')
    time_taken = problem_created_at - request_created_at
    time_taken = time_taken.total_seconds()
    generate_time_takes.append(time_taken)

print("generate_time_takes=", generate_time_takes)

print("len(generate_time_takes)=", len(generate_time_takes))
print("avg_generate_time_taken_in_minutes=", round(sum(generate_time_takes) / len(generate_time_takes) / 60, 2))







    
