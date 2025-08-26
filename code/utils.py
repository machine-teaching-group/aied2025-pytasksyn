import json
import os

def check_passed_all_tests(pytest_report_path):
    num_passed_tests = 0
    try:
        with open(pytest_report_path, 'r') as f:
            pytest_report = json.load(f)
        tests = pytest_report['tests']
        for test in tests:
            if test['call']['outcome'] == 'passed':
                num_passed_tests += 1
        if num_passed_tests>0 and num_passed_tests == pytest_report['summary']['total']:
            return True
        else:
            return False
    except:
        return False

def get_perc_passed_tests(pytest_report_path):
    try:
        with open(pytest_report_path, 'r') as f:
            pytest_report = json.load(f)
        num_passed = 0
        total_tests = pytest_report['summary']['collected']
        for key in pytest_report['tests']:
            if key['call']['outcome'] == 'passed':
                num_passed += 1
        return num_passed/total_tests*100
    except:
        return 0

def get_coverage(cov_report_path):
    try:
        with open(cov_report_path, 'r') as f:
            cov_report = json.load(f)
        return round(cov_report['totals']['percent_covered'], 2)
    except:
        return 0
    
def get_not_covered_lines(cov_report_path):
    try:
        with open(cov_report_path, 'r') as f:
            cov_report = json.load(f)
        files = cov_report['files']
        for _, file in files.items():
            return file['missing_lines'] 
    except:
        return []

def get_first_failed_test(pytest_report_path):
    failed_test_str = ''
    try:
        with open(pytest_report_path, 'r') as f:
            pytest_report = json.load(f)

        if len(pytest_report['tests']) != 0:
            for key in pytest_report['tests']:
                if key['outcome'] == 'failed':
                    failed_test_str += key['nodeid'].split('::')[1] + ' -- ' + key['call']['crash']['message'] + '\n'
                elif key['outcome'] == 'error':
                    failed_test_str += key['nodeid'].split('::')[1] + ' -- ' + key['setup']['crash']['message'] + '\n'
        else:
            failed_test_str = 'Code is not executable'
        
        if failed_test_str == '':
            failed_test_str = 'All tests passed'
        return failed_test_str
    except:
        return None, None

def get_testsuite_feedback(task_path):
    feedback = ''
    ta_testsuite_path = os.path.join(task_path, 'simulated_tutors_testsuite')
    ta_paths = sorted(os.listdir(ta_testsuite_path), key=lambda x: int(x.split('_')[-1]))
    for ta_path in ta_paths:
        ta_id = ta_path.split('_')[-1]
        if os.path.isdir(os.path.join(ta_testsuite_path, ta_path)):
            pytest_report_path = os.path.join(ta_testsuite_path, ta_path, 'pytest_report.json')
            pytest_cov_report_path = os.path.join(ta_testsuite_path, ta_path, 'pytest_coverage_report.json')
            not_covered_lines = get_not_covered_lines(pytest_cov_report_path)
            failed_test_str = get_first_failed_test(pytest_report_path)
            coverage = get_coverage(pytest_cov_report_path)

            if failed_test_str == 'All tests passed' and coverage == 100:
                continue
            else:
                feedback += f'\n# Tutor {ta_id}\n'
                if failed_test_str != 'All tests passed':
                    feedback += f'Failed test: {failed_test_str}\n'
                feedback += f'Statement coverage: {coverage}%\n'
                if coverage != 100:
                    feedback += f'Not covered lines: {not_covered_lines}\n'
                    # load program.py
                    with open(os.path.join(ta_testsuite_path, ta_path, 'program.py'), 'r') as f:
                        program_code = f.read()
                    feedback += f'Program code:\n {program_code}\n'
        
    return feedback

def get_student_feedback(task_path):
    feedback = ''
    student_path = os.path.join(task_path, 'simulated_students')
    students = sorted(os.listdir(student_path), key=lambda x: int(x.split('_')[-1]))
    for stu in students:
        student_id = stu.split('_')[-1]
        if os.path.isdir(os.path.join(student_path, stu)):
            
            with open(os.path.join(student_path, stu, 'test_results.txt'), 'r') as f:
                test_results = f.read()
            if '=================================== FAILURES ===================================' in test_results:
                feedback += f'\n# Student {student_id}\n'
                feedback += test_results.split('=================================== FAILURES ===================================')[1].split('--------------------------------- JSON report ----------------------------------')[0]
            else:
                continue
    return feedback



def get_context_feedback(task_path):
    feedback = ''
    ta_context_path = os.path.join(task_path, 'simulated_tutors')
    ta_paths = sorted(os.listdir(ta_context_path), key=lambda x: int(x.split('_')[-1]))
    for ta_path in ta_paths:
        ta_id = ta_path.split('_')[-1]
        annotations_path = os.path.join(ta_context_path, ta_path, 'annotations.json')
        with open(annotations_path, 'r') as f:
            annotations = json.load(f)
        
        reasoning = annotations['reasoning']
        q_context = annotations['q_context']
        if q_context != 1.0:
            feedback += f'\n# Tutor {ta_id}\n'
            feedback += f'Q-Context: {q_context}\n'
            feedback += f'Reasoning: {reasoning}\n'
    return feedback