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
from scipy.stats import chi2_contingency
plt.rcParams.update({'font.size': 50})
plt.rc('text', usetex=True)

main_techniques = [
    'Base',
    'GenConsistency',
    'LLMJudge',
]

all_legend_techniques = ['Base', 'GenConsistency', 'LLMJudge', 'PyTaskSyn', 'Oracle']

technique_name_to_latex_format = {
    'Base': '\\textsc{Base}',
    'GenConsistency': '\\textsc{GenConsistency}',
    'LLMJudge': '\\textsc{LLMJudge}',
    'PyTaskSyn': '\\textsc{PyTaskSyn}$_{\\tau}$',
    'Oracle': '\\textsc{Oracle}$_{p}$'
}

def create_scatter_plot(final_q_overall, coverage, final_oracle_precision, final_oracle_coverages, N, ax, i):
    markers = ['s', 'o', '^', 's', 'd',  '*',]
    colors = ['darkkhaki', 'orange', 'green', 'blue', 'red', 'purple',]
    
    k = 0
    for technique in main_techniques:
        ax.scatter([final_q_overall[technique]],[coverage[technique]], 
                   s=1800,
                   label=technique, 
                   alpha=1,
                   marker=markers[k], 
                   color=colors[k],
                   edgecolors='white',
                   linewidth=4)
        k += 1
    
    thresholds = [0, 50, 100]
    q_overall_values = []
    coverage_values = []
    for threshold in thresholds:
        technique_name = f'PyTaskSyn-{threshold}%'
        if technique_name in final_q_overall and technique_name in coverage:
            q_overall_values.append(final_q_overall[technique_name])
            coverage_values.append(coverage[technique_name])

    ax.plot(q_overall_values, coverage_values, color='royalblue', linewidth=6, marker='*', markeredgecolor='white', markeredgewidth=3, markersize=50, alpha=1, label='PyTaskSyn')
    ax.plot(final_oracle_precision, final_oracle_coverages, color='purple', linewidth=5, marker='+', markersize=30, markeredgewidth=4, alpha=0.5, label='Oracle')

    ax.set_xlim(15, 107)
    ax.set_ylim(15, 107)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xticks([20, 40, 60, 80, 100])

    ax.yaxis.set_label_coords(-0.2, 0.5)
    ax.xaxis.set_label_coords(0.5, -0.2)
    ax.set_title(f'N = {N}', fontsize=50)
    ax.set_facecolor('#e9e9e9')
    ax.grid(True, alpha=1, color='white')
    return ax.get_legend_handles_labels()

def create_complete_legend():
    """Create legend handles and labels for all techniques regardless of plotting"""
    import matplotlib.patches as mpatches
    import matplotlib.lines as mlines
    
    handles = []
    labels = []
    
    technique_styles = {
        'Base': {'marker': 's', 'color': 'darkkhaki'},
        'GenConsistency': {'marker': 'o', 'color': 'orange'}, 
        'LLMJudge': {'marker': '^', 'color': 'green'},
        'PyTaskSyn': {'marker': '*', 'color': 'royalblue'},
        'Oracle': {'marker': '+', 'color': 'purple'}
    }
    
    for technique in all_legend_techniques:
        style = technique_styles.get(technique, {'marker': 'o', 'color': 'black'})
        
        if technique == 'PyTaskSyn':
            # Line plot style for PyTaskSyn
            handle = mlines.Line2D([], [], color=style['color'], marker=style['marker'], 
                                 linewidth=6, markeredgecolor='white', markeredgewidth=4, 
                                 markersize=50, alpha=1)
        elif technique == 'Oracle':
            # Line plot style for Oracle
            handle = mlines.Line2D([], [], color=style['color'], marker=style['marker'], 
                                 linewidth=5, markersize=50, markeredgewidth=4, alpha=0.5)
        else:
            # Scatter plot style for other techniques
            handle = mlines.Line2D([], [], marker=style['marker'], color='w',
                                 markerfacecolor=style['color'], markersize=50,
                                 markeredgecolor='white', markeredgewidth=4, linestyle='None')
        
        handles.append(handle)
        labels.append(technique_name_to_latex_format[technique])
    
    return handles, labels

def summarize(data_path, annotations_1, annotations_2, metrics):
    metric = 'Q-Overall'
    fig, axs = plt.subplots(1, 2, figsize=(20, 9))

    print(f'Analyzing for {metric}...')
    for i, N in enumerate([5, 10]):
        print(f'\n\n\n\n ==== N = {N} ====')
        
        quality_annotations_1 = {}
        coverage = {}
        quality_annotations_2 = {}
        q_overall_values = {}
        contingency_table = pd.DataFrame(columns=['technique', 'technique_good_expert_good', 'technique_good_expert_bad', 'technique_bad_expert_good', 'technique_bad_expert_bad'])
        queries = [folder for folder in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, folder))]

        oracle_quality_from_two_experts = []
        oracle_coverage = []
        aggreement_frequency = {}
        for query in queries:
            if not os.path.isdir(os.path.join(data_path, query)): continue
            query_path = os.path.join(data_path, query)
            with open(os.path.join(query_path, 'passed_tasks_for_each_technique.json'), 'r') as f:
                passed_tasks_at_N = json.load(f)[str(N)]
        
            for technique, passed_tasks in passed_tasks_at_N.items():
                if technique == 'Base':
                    max_quality_by_experts = 0
                    for task in passed_tasks:
                        quality_by_expert_1 = annotations_1[(annotations_1['query'] == query) & (annotations_1['task'] == task)]['Q-Overall'].values[0]
                        quality_by_expert_2 = annotations_2[(annotations_2['query'] == query) & (annotations_2['task'] == task)]['Q-Overall'].values[0]
                        max_quality_by_experts = max(max_quality_by_experts, (quality_by_expert_1 + quality_by_expert_2) / 2)

                    if max_quality_by_experts == 1.0:
                        oracle_coverage.append(1.0)
                    else:
                        oracle_coverage.append(0.0)
                    oracle_quality_from_two_experts.append(max_quality_by_experts)
                    
                if technique not in aggreement_frequency:
                    aggreement_frequency[technique] = {'technique_good_expert_good': 0, 'technique_good_expert_bad': 0, 'technique_bad_expert_good': 0, 'technique_bad_expert_bad': 0}
        
                if technique not in coverage:
                    coverage[technique] = 0
                if technique not in q_overall_values:
                    q_overall_values[technique] = []
                if technique not in quality_annotations_1:
                    quality_annotations_1[technique] = []
                
                for task in annotations_1[annotations_1['query'] == query]['task'].values:
                    qoverall_by_expert_1 = annotations_1[(annotations_1['query'] == query) & (annotations_1['task'] == task)]['Q-Overall'].values[0]
                    qoverall_by_expert_2 = annotations_2[(annotations_2['query'] == query) & (annotations_2['task'] == task)]['Q-Overall'].values[0]
                    overall_by_expert = 1 if qoverall_by_expert_1 == 1.0 and qoverall_by_expert_2 == 1.0 else 0.0
                    if task in passed_tasks:
                        overall_by_technique = 1
                    else:
                        overall_by_technique = 0
                    if overall_by_expert == 1 and overall_by_technique == 1:
                        aggreement_frequency[technique]['technique_good_expert_good'] += 1
                    elif overall_by_expert == 0 and overall_by_technique == 1:
                        aggreement_frequency[technique]['technique_good_expert_bad'] += 1
                    elif overall_by_expert == 1 and overall_by_technique == 0:
                        aggreement_frequency[technique]['technique_bad_expert_good'] += 1
                    elif overall_by_expert == 0 and overall_by_technique == 0:
                        aggreement_frequency[technique]['technique_bad_expert_bad'] += 1
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
        print("avg_precision_from_two_annotations=", avg_precision_from_two_annotations)
        final_q_overall = {}
        for technique in avg_precision_from_two_annotations:
            final_q_overall[technique] = round(np.mean(avg_precision_from_two_annotations[technique]) * 100, 1)

        print("Q-Overall=", final_q_overall)

        std_error = {}
        for technique in avg_precision_from_two_annotations:
            std_error[technique] = round(np.std(avg_precision_from_two_annotations[technique]) / np.sqrt(len(avg_precision_from_two_annotations[technique])) * 100, 1)

        print("std_error=", std_error)

        for technique in coverage:
            coverage[technique] = round(coverage[technique] / len(queries) * 100, 1)
        print("Coverage=", coverage)
        
        #============== SCATTER PLOT ===============
        print("oracle_quality_from_two_experts", oracle_quality_from_two_experts)
        print("oracle_coverage", oracle_coverage)
        oracle_quality_from_two_experts, oracle_coverage = zip(*sorted(zip(oracle_quality_from_two_experts, oracle_coverage), reverse=True))
        print("oracle_quality_from_two_experts=", oracle_quality_from_two_experts)
        print("oracle_coverage=", oracle_coverage)
        num_ones = sum(1 for quality in oracle_quality_from_two_experts if quality == 1.0)
        print("Number of 1s in oracle_quality_from_two_experts:", num_ones)

        final_oracle_precision = []
        final_oracle_precision_std_error = []
        final_oracle_coverages = []

        for k in range(num_ones, len(oracle_quality_from_two_experts)+1):
            pre = round(np.mean(oracle_quality_from_two_experts[:k]) * 100, 1)
            oracle_precision_std_error = round(np.std(oracle_quality_from_two_experts[:k]) / np.sqrt(k) * 100, 1)
            print(len(oracle_coverage))
            cov = round(len(oracle_coverage[:k])/len(oracle_coverage) * 100, 1)
            final_oracle_precision.append(pre)
            final_oracle_precision_std_error.append(oracle_precision_std_error)
            final_oracle_coverages.append(cov)

        print("final_oracle_precision=", final_oracle_precision)
        print("final_oracle_precision_std_error=", final_oracle_precision_std_error)
        print("final_oracle_coverages=", final_oracle_coverages)

        create_scatter_plot(final_q_overall, coverage, final_oracle_precision, final_oracle_coverages, N, axs[i], i)
        
        if i == 0:
            axs[i].set_ylabel('Coverage (\%)')
            axs[i].set_xlabel('Precision (\%)')

        #===== Chi-square test =====
        if N==10:
            for technique in aggreement_frequency:
                contingency_table.loc[len(contingency_table)] = [
                    technique,
                    aggreement_frequency[technique]['technique_good_expert_good'],
                    aggreement_frequency[technique]['technique_good_expert_bad'],
                    aggreement_frequency[technique]['technique_bad_expert_good'],
                    aggreement_frequency[technique]['technique_bad_expert_bad']
                ]
            print("contingency_table=", contingency_table)
            for technique in main_techniques:
                contingency_table_for_technique = contingency_table[contingency_table['technique'] == technique]
                contingency_table_for_main_technique = contingency_table[contingency_table['technique'] == 'PyTaskSyn-50%']
                
                # Check if dataframes are empty before accessing values
                if not contingency_table_for_technique.empty and not contingency_table_for_main_technique.empty:
                    chi_square_statistic, p_value, dof, expected = chi2_contingency([
                        contingency_table_for_technique.iloc[0, 1:].values,
                        contingency_table_for_main_technique.iloc[0, 1:].values
                    ])
                    print(f"Chi-square statistic for {technique}: {chi_square_statistic}")
                    print(f"P-value for {technique}: {p_value}")
                    print(f"Degrees of freedom for {technique}: {dof}")
                    print(f"Expected frequencies for {technique}: {expected}")
                else:
                    print(f"No data available for chi-square test for {technique}")

    # Create complete legend with all methods
    handles, labels = create_complete_legend()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=5, fontsize=35, columnspacing=0.8, handletextpad=0.3)
    plt.tight_layout()
    plt.savefig('plots/precision-coverage.pdf', bbox_inches='tight')
    plt.clf()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, default='outputs', help='path to the experiment')
    args = parser.parse_args()

    metrics = ['Q-Testsuite', 'Q-Context','Q-Comprehensible','Q-Overall']
    annotation_file_1 = os.path.join(args.data_path, 'annotations_expert_1.csv')
    annotation_1 = pd.read_csv(annotation_file_1)

    annotation_file_2 = os.path.join(args.data_path, 'annotations_expert_2.csv')
    annotation_2 = pd.read_csv(annotation_file_2)

    summarize(args.data_path, annotation_1, annotation_2, metrics)
