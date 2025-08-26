#=============== STAGE 1: Expert generation ===============

system_prompt_expert = "You are an expert in Python programming."
user_prompt_expert = "Given a theme of '{theme}', generate a Python programming task that requires only {concepts} to solve. The task should include a task description, a test suite, and a solution program.\n\
- The task must be clearly relevant to the given theme of {theme} and the theme is explicitly used throughout. Only the given programming concepts of {concepts} are strictly required to solve the task.\n\
- The task description must be sensible and sound natural. It must provide comprehensive information required to solve the task and pass the test suite (e.g., how the program will be tested, function signatures). Do not use type hints. Do not mention the required programming concepts in the task description.\n\
- The test suite must consist of at least 5 comprehensive test cases written in the Pytest framework format. The testsuite must be correct and covers both base and corner cases. If the test suite involves handling files and I/O, the related files should be created using `setup_module()` and removed using `teardown_module()` functions in the Pytest framework. Everything from the solution program will be imported manually; do not import anything else except `pytest` and `os`. Do not use multiple assert statements in a single test case.\n\
- The solution program must use only the given programming concepts of {concepts}. It should not include any comments, usage examples, or tests.\n\
Output a JSON object with the following keys: 'task_description', 'test_suite', and 'solution_program'. Do not require any other programming concepts than {concepts} to solve the task. If 'dictionary' is not given, do not require it for solving the task."


#=============== STAGE 2a: Tutor validation ===============
system_prompt_tutor = "You are a tutor in a Python programming course."
user_prompt_tutor = "The following Python programming task was created given a theme of '{theme}' and a list of programming concepts {concepts}:\n\n\
### Beginning of task description\n\
{task_description}\n\
### End of task description\n\n\
### Beginning of test suite\n\
{test_suite}\n\
### End of test suite\n\n\
Write a program to solve the task and evaluate the context relevance of the task. The context relevance is 1 if the task is clearly relevant to the given theme and the theme is explicitly used throughout, and all given programming concepts are strictly required to solve the task; 0 otherwise.\n\
Output a JSON object with the following keys: 'program', 'context_relevance'. Note that comparison operators are not arithmetic operators."

#=============== STAGE 2b: Student validation ===============
system_prompt_student = "You are a student enrolled in a Python programming course."
user_prompt_student = "Write a program to solve the task below.\n\n\
### Beginning of task description\n\
{task_description}\n\
### End of task description\n\n\
Do not include example usages, comments, or tests.\n\
Output a JSON object with the following key: 'program'."

#=============== BASELINE: LLMJudge ===============
system_prompt_judge = "You are an expert in Python programming."
user_prompt_judge = "The following Python programming task was created given a context of '{theme}' and a list of programming concepts {concepts}:\n\n\
### Beginning of task description\n\
{task_description}\n\
### End of task description\n\n\
### Beginning of test suite\n\
{test_suite}\n\
### End of test suite\n\n\
Evaluate the quality of the task using the following rubric:\n\
- Q-Testsuite: 1 if the test suite is correct and covers both base cases and corner cases; 0 otherwise.\n\
- Q-Context: 1 if the task is clearly relevant to the given theme and the theme is explicitly used throughout, and all given programming concepts are strictly required to solve the task; 0 otherwise.\n\
- Q-Comprehensible: 1 if all information needed to solve the task (passing the test suite) is provided in the task description; 0 otherwise.\n\
- Q-Overall: 1 if all the individual quality metrics listed above are 1; 0 otherwise.\n\
Output a JSON object with the following keys: 'q_testsuite', 'q_context', 'q_comprehensible', and 'q_overall'."

#=============== FEEDBACK LOOP ===============
system_prompt_feedback_loop = "You are an expert in Python programming."
user_prompt_feedback_loop = "The following Python programming task was created given a theme of '{theme}' and a list of programming concepts {concepts}. Below are the task quality requirements and the evaluation feedback. Update the task to improve its quality based on the feedback.\n\n\
### Task quality requirements\n\
- The task must be clearly relevant to the given theme of {theme} and the theme is explicitly used throughout. Only the given programming concepts of {concepts} are strictly required to solve the task.\n\
- The task description must be sensible and sound natural. It must provide comprehensive information required to solve the task and pass the test suite (e.g., how the program will be tested, function signatures). Do not use type hints. Do not mention the required programming concepts in the task description.\n\
- The test suite must consist of at least 5 comprehensive test cases written in the Pytest framework format. The testsuite must be correct and covers both base and corner cases. If the test suite involves handling files and I/O, the related files should be created using `setup_module()` and removed using `teardown_module()` functions in the Pytest framework. Everything from the solution program will be imported manually; do not import anything else except `pytest` and `os`.\n\
- The solution program must use only the given programming concepts of {concepts}. It should not include any comments, usage examples, or tests.\n\n\
### Task description\n\
{task_description}\n\n\
### Test suite\n\
{test_suite}\n\n\
### Testsuite feedback ===\n\
{testsuite_feedback}\n\n\
### Context feedback ===\n\
{context_feedback}\n\n\
### Comprehensibility feedback ===\n\
{student_feedback}\n\n\
Think step by step and output the updated task as a JSON object with the following keys: 'reasoning', 'task_description', 'test_suite', and 'solution_program'."