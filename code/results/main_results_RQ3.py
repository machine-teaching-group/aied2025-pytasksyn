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
plt.rcParams.update({'font.size': 55})
plt.rc('text', usetex=True)

main_techniques = ['Base',
            'LLMJudge',
            'GenConsistency',
            'SimTutorsVal',
            'PyTaskSyn-50%'
]

technique_name_to_latex_format = {
    'Base': '\\textsc{Base}',
    'GenConsistency': '\\textsc{GenConsistency}',
    'LLMJudge': '\\textsc{LLMJudge}',
    'SimTutorsVal': '\\textsc{SimTutorsVal}',
    'SimStudentsVal': '\\textsc{SimStudentsVal}',
    'PyTaskSyn-50%': '\\textsc{PyTaskSyn}$_{\\tau=50\%}$',
    'PyTaskSyn': '\\textsc{PyTaskSyn}$_{\\tau}$',
    'Oracle': '\\textsc{Oracle}$_{p}$'
}

def summarize(data_path, annotations_1, annotations_2, metrics):
    metric = 'Q-Overall'

    print(f'Analyzing for {metric}...')
    for i, N in enumerate([1, 5, 10]):
        print(f'\n\n\n\n ==== N = {N} ====')
        if N!=10:
            continue
        coverage = {}
        queries = [folder for folder in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, folder))]

        theme_counts = {}
        theme_counts_high_quality = {}
        concept_counts = {}
        concept_counts_high_quality = {}
        for query in queries:
            if not os.path.isdir(os.path.join(data_path, query)): continue
            query_path = os.path.join(data_path, query)
            with open(os.path.join(query_path, 'passed_tasks_for_each_technique.json'), 'r') as f:
                passed_tasks_at_N = json.load(f)[str(N)]
            # load theme
            with open(os.path.join(query_path, 'theme.txt'), 'r') as f:
                theme = f.read()
            # load concepts
            with open(os.path.join(query_path, 'programming_concepts.txt'), 'r') as f:
                concepts = eval(f.read())
            for technique, passed_tasks in passed_tasks_at_N.items():
                if technique == 'PyTaskSyn-50%':
                    if theme not in theme_counts:
                        theme_counts[theme] = []
                    if theme not in theme_counts_high_quality:
                        theme_counts_high_quality[theme] = []
                    theme_counts[theme].append(len(passed_tasks))
                    for concept in concepts:
                        if concept not in concept_counts:
                            concept_counts[concept] = []
                        if concept not in concept_counts_high_quality:
                            concept_counts_high_quality[concept] = []
                        concept_counts[concept].append(len(passed_tasks))
                    high_quality_counts = 0
                    for task in passed_tasks:
                        qoverall_by_expert_1 = annotations_1[(annotations_1['query'] == query) & (annotations_1['task'] == task)]['Q-Overall'].values[0]
                        qoverall_by_expert_2 = annotations_2[(annotations_2['query'] == query) & (annotations_2['task'] == task)]['Q-Overall'].values[0]
                        overall_by_expert = 1.0 if qoverall_by_expert_1 == 1.0 and qoverall_by_expert_2 == 1.0 else 0.0
                        if overall_by_expert == 1.0:
                            high_quality_counts += 1
                    
                    theme_counts_high_quality[theme].append(high_quality_counts)
                    for concept in concepts:
                        concept_counts_high_quality[concept].append(high_quality_counts)

        print("Theme counts =", theme_counts)
        print("Theme counts high quality =", theme_counts_high_quality)
        avg_theme_counts = {theme: sum(counts) / len(counts) for theme, counts in theme_counts.items()}
        std_error_theme_counts = {theme: np.std(counts) / np.sqrt(len(counts)) for theme, counts in theme_counts.items()}
        avg_theme_counts_high_quality = {theme: sum(counts) / len(counts) for theme, counts in theme_counts_high_quality.items()}
        std_error_theme_counts_high_quality = {theme: np.std(counts) / np.sqrt(len(counts)) for theme, counts in theme_counts_high_quality.items()}

        print("Average theme counts =", avg_theme_counts)
        print("Average theme counts high quality =", avg_theme_counts_high_quality)
        print("Std error theme counts =", std_error_theme_counts)
        print("Std error theme counts high quality =", std_error_theme_counts_high_quality)
        
        avg_concept_counts = {concept: sum(counts) / len(counts) for concept, counts in concept_counts.items()}
        std_error_concept_counts = {concept: np.std(counts) / np.sqrt(len(counts)) for concept, counts in concept_counts.items()}
        avg_concept_counts_high_quality = {concept: sum(counts) / len(counts) for concept, counts in concept_counts_high_quality.items()}
        std_error_concept_counts_high_quality = {concept: np.std(counts) / np.sqrt(len(counts)) for concept, counts in concept_counts_high_quality.items()}
       
        # Set consistent font sizes
        TITLE_SIZE = 70
        LABEL_SIZE = 70
        TICK_SIZE = 70
        BAR_WIDTH = 0.4

        # Create a common legend
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(55, 5), gridspec_kw={'width_ratios': [1.1, 2.2], 'wspace': 0.05})

        # Plot 1: Theme counts
        ax1.set_facecolor('#f8f8f8')  # Light gray background
        themes = ["Science Fiction", "Cooking", "Game of Chance", 'Superheroes', "Board Games"]
        # reorder the theme in avg_theme_counts
        avg_theme_counts_ordered = {theme: avg_theme_counts[theme] for theme in themes}
        std_error_theme_counts_ordered = {theme: std_error_theme_counts[theme] for theme in themes}
        avg_theme_counts_high_quality_ordered = {theme: avg_theme_counts_high_quality[theme] for theme in themes}
        std_error_theme_counts_high_quality_ordered = {theme: std_error_theme_counts_high_quality[theme] for theme in themes}

        themes = list(avg_theme_counts_ordered.keys())
        x = np.arange(len(themes))
        rects1 = ax1.bar(x - BAR_WIDTH/2, avg_theme_counts_ordered.values(), BAR_WIDTH, label='Tasks passed validation', color='orange', alpha=0.95, edgecolor='black', linewidth=4, yerr=list(std_error_theme_counts_ordered.values()), capsize=0, error_kw={'elinewidth': 6, 'capthick': 0}, hatch='.')
        rects2 = ax1.bar(x + BAR_WIDTH/2, avg_theme_counts_high_quality_ordered.values(), BAR_WIDTH, label='Tasks passed validation and rated high-quality by experts', color='dodgerblue', alpha=0.95, edgecolor='black', linewidth=4, yerr=list(std_error_theme_counts_high_quality_ordered.values()), capsize=0, error_kw={'elinewidth': 6, 'capthick': 0}, hatch='/')
        ax1.set_ylabel('Avg. \#tasks', fontsize=LABEL_SIZE)
        ax1.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
        ax1.set_xticks(x)
        themes_names = ["Science\n fiction", "Cooking", "Game \nof Chance", 'Super-\nheroes', "Board\n games"]
        ax1.set_xticklabels(themes_names, fontsize=55)
        ax1.text(0.5, -0.6, '(a) By theme', transform=ax1.transAxes, ha='center', va='center', fontsize=75)
        ax1.grid(True, alpha=0.5)

        # Plot 2: Concept counts
        ax2.set_facecolor('#f8f8f8') 
        print("Concept counts =", avg_concept_counts)
        # reorder the concept in avg_concept_counts
        concepts = ["Arithmetic Operators", "Variables", "Selection Statements (if/else, etc.)", 'Loops', "File Handling and I/O", "Lists", "Exception Handling", 'Dictionaries', "Classes and Objects", "Strings"]
        avg_concept_counts_ordered = {concept: avg_concept_counts[concept] for concept in concepts}
        std_error_concept_counts_ordered = {concept: std_error_concept_counts[concept] for concept in concepts}
        avg_concept_counts_high_quality_ordered = {concept: avg_concept_counts_high_quality[concept] for concept in concepts}
        std_error_concept_counts_high_quality_ordered = {concept: std_error_concept_counts_high_quality[concept] for concept in concepts}
        concepts = list(avg_concept_counts_ordered.keys())
        x = np.arange(len(concepts))
        rects3 = ax2.bar(x - BAR_WIDTH/2, avg_concept_counts_ordered.values(), BAR_WIDTH, label='Generated tasks', color='orange', alpha=0.95, edgecolor='black', linewidth=4, yerr=list(std_error_concept_counts_ordered.values()), capsize=0, error_kw={'elinewidth': 6, 'capthick': 0}, hatch='.')
        rects4 = ax2.bar(x + BAR_WIDTH/2, avg_concept_counts_high_quality_ordered.values(), BAR_WIDTH, label='Generated tasks rated high-quality by experts', color='dodgerblue', alpha=0.95, edgecolor='black', linewidth=4, yerr=list(std_error_concept_counts_high_quality_ordered.values()), capsize=0, error_kw={'elinewidth': 6, 'capthick': 0}, hatch='/')
        ax2.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
        ax2.set_xticks(x)

        concepts = ["Arith.\n operators", "Variables", "Select.\n statements", 'Loops', "Files \n \& I/O", "Lists", "Exception\n handling", 'Dict.',   "Classes\n\& objects", "String"]
        ax2.set_xticklabels(concepts, fontsize=55)

        ax2.grid(True, alpha=0.5)
        ax2.text(0.5, -0.6, '(b) By programming concepts', transform=ax2.transAxes, ha='center', va='center', fontsize=75)

        # Set axis limits
        ax1.set_xlim(-0.5, 4.5)
        ax2.set_xlim(-0.5, 9.5)
        ax1.set_ylim(0, 5)
        ax1.set_yticks([0, 2, 4])
        ax2.set_ylim(0, 5)
        ax2.set_yticks([0, 2, 4])

        # Add legend
        handles, labels = ax1.get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.4), 
                  ncol=2, fontsize=TICK_SIZE)

        # Save and close plot
        plt.tight_layout()
        plt.savefig('plots/theme_and_concept_counts.pdf', bbox_inches='tight')
        plt.close()


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
