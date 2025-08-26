import os
import json
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})
from scipy.stats import norm
import numpy as np
from scipy.stats import truncnorm
import random
np.random.seed(200)
import csv
from matplotlib.patches import Rectangle
plt.rcParams.update({'font.size': 53})
plt.rc('text', usetex=True)

main_techniques = ['Base',
            # 'GenConsistency',
            # 'LLMJudge',
            'SimTutorsVal',
            'SimStudentsVal-50%',
            'PyTaskSyn-50%'
]

technique_name_to_latex_format = {
    'Base': '\\textsc{Base}',
    'GenConsistency': '\\textsc{GenConsistency}',
    'LLMJudge': '\\textsc{LLMJudge}',
    'SimTutorsVal': 'Only \\textsc{SimTutors}',
    'SimStudentsVal': 'Only  \\textsc{SimStudent}',
    'PyTaskSyn-50%': '\\textsc{PyTaskSyn}',
    'SimStudentsVal-50%': 'Only \\textsc{SimStudent}',
    'PyTaskSyn': '\\textsc{PyTaskSyn}$_{\\tau}$',
    'Oracle': '\\textsc{Oracle}$_{p}$'
}

def summarize(data_path, annotations_1, annotations_2, metrics):
    metric = 'Q-Overall'
    fig, axs = plt.subplots(1, 3, figsize=(30, 12))
    handles, labels = [], []

    print(f'Analyzing for {metric}...')
    for i, N in enumerate([1, 5, 10]):
        print(f'\n\n\n\n ==== N = {N} ====')
        
        quality_annotations_1 = {}
        precision_annotations_1 = {}
        coverage = {}

        quality_annotations_2 = {}
        precision_annotations_2 = {}

        difficulty = {}
        standard_error = {}
        difficulties = {}
        q_overall_values = {}
        contingency_table = pd.DataFrame(columns=['technique', 'technique_good_expert_good', 'technique_good_expert_bad'])
        queries = [folder for folder in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, folder))]

        aggreement_frequency = {}
        for query in queries:
            if not os.path.isdir(os.path.join(data_path, query)): continue
            query_path = os.path.join(data_path, query)
            with open(os.path.join(query_path, 'passed_tasks_for_each_technique.json'), 'r') as f:
                passed_tasks_at_N = json.load(f)[str(N)]
        
            for technique, passed_tasks in passed_tasks_at_N.items():
                if technique not in main_techniques:
                    continue
                if technique not in aggreement_frequency:
                    aggreement_frequency[technique] = {'technique_good_expert_good': 0, 'technique_good_expert_bad': 0, 'technique_bad_expert_good': 0, 'technique_bad_expert_bad': 0}
        
                if technique not in coverage:
                    coverage[technique] = 0
                if technique not in q_overall_values:
                    q_overall_values[technique] = []
                if technique not in quality_annotations_1:
                    quality_annotations_1[technique] = []
                
                for task in passed_tasks:
                    qoverall_by_expert_1 = annotations_1[(annotations_1['query'] == query) & (annotations_1['task'] == task)]['Q-Overall'].values[0]
                    qoverall_by_expert_2 = annotations_2[(annotations_2['query'] == query) & (annotations_2['task'] == task)]['Q-Overall'].values[0]
                    overall_by_expert = 1 if qoverall_by_expert_1 == 1.0 and qoverall_by_expert_2 == 1.0 else 0.0
                    overall_by_technique = 1
                    if overall_by_expert == 1 and overall_by_technique == 1:
                        aggreement_frequency[technique]['technique_good_expert_good'] += 1
                    elif overall_by_expert == 0 and overall_by_technique == 1:
                        aggreement_frequency[technique]['technique_good_expert_bad'] += 1
                if len(passed_tasks) > 0:
                    coverage[technique] += 1

                if technique not in quality_annotations_1:
                    quality_annotations_1[technique] = []
                if technique not in quality_annotations_2:
                    quality_annotations_2[technique] = []

                passed_qualities_annotations_1 = []
                passed_qualities_annotations_2 = []
                for passed_task in passed_tasks:
                    passed_qualities_annotations_1.append(annotations_1[(annotations_1['query'] == query) & (annotations_1['task'] == passed_task)][metric].values[0])
                    passed_qualities_annotations_2.append(annotations_2[(annotations_2['query'] == query) & (annotations_2['task'] == passed_task)][metric].values[0])
             
                if len(passed_tasks) > 0:
                    mean_passed_quality_annotations_1 = np.mean(passed_qualities_annotations_1)
                    mean_passed_quality_annotations_2 = np.mean(passed_qualities_annotations_2)

                    quality_annotations_1[technique].append(mean_passed_quality_annotations_1)
                    quality_annotations_2[technique].append(mean_passed_quality_annotations_2)
        
        avg_precision_from_two_annotations = {}
        for technique in quality_annotations_1:
            avg_precision_from_two_annotations[technique] = [
                (q1 + q2) / 2 
                for q1, q2 in zip(quality_annotations_1[technique], quality_annotations_2[technique])
            ]

        final_q_overall = {}
        for technique in avg_precision_from_two_annotations:
            final_q_overall[technique] = np.mean(avg_precision_from_two_annotations[technique])

        print("Q-Overall=", final_q_overall)

        std_error = {}
        for technique in avg_precision_from_two_annotations:
            std_error[technique] = np.std(avg_precision_from_two_annotations[technique]) / np.sqrt(len(avg_precision_from_two_annotations[technique]))

        print("std_error=", std_error)

        for technique in coverage:
            coverage[technique] = coverage[technique] / len(queries)
        print("Coverage=", coverage)

    #========== HEATMAP ===========
    metrics = ['Q-Overall', 'Q-Testsuite','Q-Context','Q-Comprehensible',]
    pd_data = pd.DataFrame(columns=['Technique'] + metrics)
    N = 10
    queries = [folder for folder in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, folder))]
    metric_values = {}
    for query in queries:
        if not os.path.isdir(os.path.join(data_path, query)): continue
        query_path = os.path.join(data_path, query)
        with open(os.path.join(query_path, 'passed_tasks_for_each_technique.json'), 'r') as f:
            passed_tasks_at_N = json.load(f)[str(N)]
        for technique, passed_tasks in passed_tasks_at_N.items():
            if technique not in main_techniques:
                continue
            if technique not in metric_values:
                metric_values[technique] = {}
                for metric in metrics:
                    metric_values[technique][metric] = []
            filtered_annotations_1 = annotations_1[(annotations_1['query'] == query) & (annotations_1['task'].isin(passed_tasks))]
            filtered_annotations_2 = annotations_2[(annotations_2['query'] == query) & (annotations_2['task'].isin(passed_tasks))]

            if len(passed_tasks) > 0:
                for metric in metrics:
                    mean_metric_by_expert_1 = filtered_annotations_1[metric].replace(np.NaN, 0).mean()
                    mean_metric_by_expert_2 = filtered_annotations_2[metric].replace(np.NaN, 0).mean()
                    mean_metric_by_experts = (mean_metric_by_expert_1 + mean_metric_by_expert_2) / 2
                    metric_values[technique][metric].append(mean_metric_by_experts)

    print("metric_values=", metric_values)
    for technique in main_techniques:
        
        avg_metric_values = {metric: sum(metric_values[technique][metric])/len(metric_values[technique][metric]) for metric in metrics}
        print("avg_metric_values=", avg_metric_values)
        pd_data = pd.concat([pd_data, pd.DataFrame([[technique] + [avg_metric_values[metric] for metric in metrics]], columns=['Technique'] + metrics)])
    
    print(pd_data)


    pd_data['Technique'] = pd_data['Technique'].apply(lambda x: technique_name_to_latex_format[x])

    # replace the column name "Q-Comprehensible" to "Q-Compre."
    pd_data.rename(columns={'Q-Testsuite': 'Test suite'}, inplace=True)
    pd_data.rename(columns={'Q-Context': 'Context relevance'}, inplace=True)
    pd_data.rename(columns={'Q-Comprehensible': 'Comprehensibility'}, inplace=True)

    fig, ax = plt.subplots(figsize=(35, 7))  
    sns.heatmap(pd_data.set_index('Technique'), cmap='Blues', annot=True, fmt=".2f", ax=ax, vmin=0, vmax=1, cbar_kws={'shrink': .8}, annot_kws={'color': 'white'})
    ax.add_patch(Rectangle((1.04, 0.95), 1.96, 1, fill=False, edgecolor='yellow', linestyle='--', linewidth=5))
   
    

    ax.add_patch(Rectangle((2.99, 2), 1, 1, fill=False, edgecolor='yellow', linestyle='--', linewidth=5))

    ax.axvline(x=1, color='white', linewidth=20)

    ax.xaxis.set_ticks_position('top')
    ax.xaxis.set_label_position('top')
    ax.tick_params(axis='y', pad=6) 
    plt.tight_layout()  
    plt.tick_params(axis='both', which='both', bottom=False, top=False)


    plt.subplots_adjust(wspace=0.5) 
    plt.tight_layout()
    plt.savefig('plots/heatmap.pdf')
    plt.clf()

if __name__=="__main__":
    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, default='outputs', help='path to the experiment')
    args = parser.parse_args()

    metrics = ['Q-Testsuite', 'Q-Context','Q-Comprehensible','Q-Overall'] 
    annotation_file_1 = os.path.join(args.data_path, 'annotations_expert_1.csv')
    annotation_1 = pd.read_csv(annotation_file_1)
    
    annotation_file_2 = os.path.join(args.data_path, 'annotations_expert_2.csv')
    annotation_2 = pd.read_csv(annotation_file_2)

    summarize(args.data_path, annotation_1, annotation_2, metrics)