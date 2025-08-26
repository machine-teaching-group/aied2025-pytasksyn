import pandas as pd
import numpy as np

def compute_agreement(expert_1_annotation, expert_2_annotation, metric):
    expert_1_annotation = expert_1_annotation[metric]
    expert_2_annotation = expert_2_annotation[metric]

    assert len(expert_1_annotation) == len(expert_2_annotation), "Annotations must be of the same length."

    values = [0.0, 1.0]
    
    contingency_table = {}
    for value_1 in values:
        for value_2 in values:
            contingency_table[(value_1, value_2)] = 0
    
    # Fill contingency table
    for i in range(len(expert_1_annotation)):
        value_1 = expert_1_annotation[i]
        value_2 = expert_2_annotation[i]
        # Handle NaN values
        if pd.isna(value_1) or pd.isna(value_2):
            continue
        if (value_1, value_2) not in contingency_table:
            print(f"Unexpected value pair: ({value_1}, {value_2})")
            continue
        contingency_table[(value_1, value_2)] += 1
    
    # Calculate row totals
    rows_total = {}
    for value_1 in values:
        rows_total[value_1] = sum(contingency_table.get((value_1, value_2), 0) for value_2 in values)
    
    # Calculate column totals
    columns_total = {}
    for value_2 in values:
        columns_total[value_2] = sum(contingency_table.get((value_1, value_2), 0) for value_1 in values)
    
    # Calculate the number of observed agreements
    number_of_agreements = sum(contingency_table.get((value, value), 0) for value in values)
        
    # Compute the expected frequency for agreements by chance
    expected_frequency = {}
    total_annotations = sum(rows_total.values())
    for value in values:
        expected_frequency[(value, value)] = (rows_total[value] * columns_total[value]) / total_annotations
    
    sum_expected_frequency = sum(expected_frequency.values())

    # Compute the agreement
    if total_annotations == sum_expected_frequency:
        agreement = 1
    else:
        agreement = (number_of_agreements - sum_expected_frequency) / (total_annotations - sum_expected_frequency)

    print(f"-------Cohen's Kappa for {metric}: {agreement}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute agreement between expert annotations')
    parser.add_argument('expert_1_annotation_path', help='Path to expert 1 annotation CSV file', default='outputs/annotations_expert_1.csv')
    parser.add_argument('expert_2_annotation_path', help='Path to expert 2 annotation CSV file', default='outputs/annotations_expert_2.csv')
    
    args = parser.parse_args()
    
    # read csvs
    expert_1_annotation = pd.read_csv(args.expert_1_annotation_path)
    expert_2_annotation = pd.read_csv(args.expert_2_annotation_path)

    # compute agreement
    metrics = ['Q-Testsuite','Q-Context','Q-Comprehensible', 'Q-Overall', 'contain_higher_level_concepts']
    for metric in metrics:
        compute_agreement(expert_1_annotation, expert_2_annotation, metric)