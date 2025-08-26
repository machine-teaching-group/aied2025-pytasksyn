import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import nest_asyncio
nest_asyncio.apply()
import time

from openai import OpenAI
from pydantic import BaseModel

OpenAI.api_key = os.environ["OPENAI_API_KEY"]
client = OpenAI()

ON_HEROKU = eval(os.environ.get("ON_HEROKU"))
if ON_HEROKU:
    from ..data.prompt_templates import *
    MAX_WORKERS = 20
else:
    from data.prompt_templates import *
    MAX_WORKERS = 20
    
# Get the directory of the current script
script_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

class TutorContext(BaseModel):
    program: str
    context_relevance: float

class Tutor_Testsuite(BaseModel):
    program: str

class JudgeAnnotation(BaseModel):
    q_testsuite: float
    q_context: float
    q_comprehensible: float
    q_overall: float
    
class StudentAttempt(BaseModel):
    program: str

def parse_student_response(output_path):
    with open(os.path.join(output_path, "response.txt"), 'r') as f:
        response = f.read()
    # save solution_program
    with open(os.path.join(output_path, "solution_program.py"), 'w') as f:
        try:
            solution_program = response.split("```python")[1].split("```")[0]
        except:
            try:
                solution_program = response.split("```")[1]
            except:
                solution_program = response
        f.write(solution_program)

def query_student(task_path, task_description, model, temp, simulated_students_path, num_students):
    ### Query the model
    prompt = user_prompt_student.format(task_description=task_description)

    completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {   
                            "role": "system", "content": system_prompt_student,
                            "role": "user", "content": prompt
                        }
                    ],
                    response_format=StudentAttempt,
                    n=num_students)
    if not ON_HEROKU:
        # Save token count to a file
        if os.path.exists(os.path.join(task_path, 'token_count.json')):
            with open(os.path.join(task_path, 'token_count.json'), 'r') as f:
                token_count = json.load(f)
        else:
            token_count = {}
        tokens = completion.usage.to_dict()
        token_count['student'] = tokens
        with open(os.path.join(task_path, 'token_count.json'), 'w') as f:
            json.dump(token_count, f, indent=4)

    for rollout in range(num_students):
        output_path = os.path.join(simulated_students_path, f"{model}_temp-{temp}_{rollout}")
        os.makedirs(output_path, exist_ok=True)

        if not ON_HEROKU:
            # Write prompt to file
            with open(os.path.join(output_path, "prompt.txt"), 'w') as f:
                f.write(system_prompt_student)
                f.write("\n\n")
                f.write(prompt)

        # Save response to a file
        response = completion.choices[rollout].message.parsed
        solution_program = response.program

        # write solution_program to file
        with open(os.path.join(output_path, "solution_program.py"), 'w') as f:
            f.write(solution_program)
    
def query_judge(task_path, theme, programming_concepts, task_description, test_suite, model, temp, judge_path, num_judges):
    prompt = user_prompt_judge.format(theme=theme, concepts=str(programming_concepts), task_description=task_description, test_suite=test_suite)
    
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt_judge},
            {"role": "user", "content": prompt}
        ],
        response_format=JudgeAnnotation,
        n=num_judges
    )
    
    for rollout, choice in enumerate(completion.choices):
        output_path = os.path.join(judge_path, f"{model}_temp-{temp}_{rollout}")
        os.makedirs(output_path, exist_ok=True)
        
        with open(os.path.join(output_path, 'prompt.txt'), 'w') as f:
            f.write(f"{system_prompt_judge}\n\n{prompt}")
        
        response = choice.message.parsed
        
        with open(os.path.join(output_path, 'annotations.json'), 'w') as f:
            json.dump(response.dict(), f, indent=4)

    # Update token count
    token_count = {}
    if os.path.exists(os.path.join(task_path, 'token_count.json')):
        with open(os.path.join(task_path, 'token_count.json'), 'r') as f:
            token_count = json.load(f)
    
    token_count['judge'] = completion.usage.dict()
    with open(os.path.join(task_path, 'token_count.json'), 'w') as f:
        json.dump(token_count, f, indent=4)

    return True

def query_simulated_students(query_path, task, model_configuration, task_dict):
    num_students = model_configuration["student"]["quantity"]
    model = model_configuration["student"]["model"]
    temp = model_configuration["student"]["temperature"]

    task_path = os.path.join(query_path, task)
    simulated_students_path = os.path.join(task_path, "simulated_students")
    os.makedirs(simulated_students_path, exist_ok=True)

    prompt = user_prompt_student.format(task_description=task_dict[task]['task_description'])

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt_student},
            {"role": "user", "content": prompt}
        ],
        response_format=StudentAttempt,
        n=num_students,
        max_tokens=4096
    )

    if not ON_HEROKU:
        # Save token count
        token_count = {}
        if os.path.exists(os.path.join(task_path, 'token_count.json')):
            with open(os.path.join(task_path, 'token_count.json'), 'r') as f:
                token_count = json.load(f)
        
        token_count['student'] = completion.usage.dict()
        with open(os.path.join(task_path, 'token_count.json'), 'w') as f:
            json.dump(token_count, f, indent=4)

    for rollout, choice in enumerate(completion.choices):
        output_path = os.path.join(simulated_students_path, f"{model}_temp-{temp}_{rollout}")
        os.makedirs(output_path, exist_ok=True)

        if not ON_HEROKU:
            with open(os.path.join(output_path, "prompt.txt"), 'w') as f:
                f.write(f"{system_prompt_student}\n\n{prompt}")

        response = choice.message.parsed
        solution_program = response.program

        with open(os.path.join(output_path, "solution_program.py"), 'w') as f:
            f.write(solution_program)

def query_simulated_tutor(query_path, theme, programming_concepts, task, model_configuration, task_dict):
    context_satisfied = True
    model = model_configuration["tutor"]["model"]
    num_tutors = model_configuration["tutor"]["quantity"]
    temp = model_configuration["tutor"]["temperature"]
    task_path = os.path.join(query_path, task)
    simulated_tutors_path = os.path.join(task_path, "simulated_tutors")
    os.makedirs(simulated_tutors_path, exist_ok=True)
    
    prompt = user_prompt_tutor.format(theme=theme, concepts=str(programming_concepts), task_description=task_dict[task]['task_description'], test_suite=task_dict[task]['test_suite'])
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt_tutor},
            {"role": "user", "content": prompt}
        ],
        response_format=TutorContext,
        n=num_tutors
    )

    if not ON_HEROKU:
        # Update token count
        token_count = {}
        if os.path.exists(os.path.join(task_path, 'token_count.json')):
            with open(os.path.join(task_path, 'token_count.json'), 'r') as f:
                token_count = json.load(f)
        
        token_count['tutor'] = completion.usage.dict()
        with open(os.path.join(task_path, 'token_count.json'), 'w') as f:
            json.dump(token_count, f, indent=4)
    
    for rollout, choice in enumerate(completion.choices):
        output_path = os.path.join(simulated_tutors_path, f"{model}_temp-{temp}_{rollout}")
        os.makedirs(output_path, exist_ok=True)
        
        if not ON_HEROKU:
            with open(os.path.join(output_path, 'prompt.txt'), 'w') as f:
                f.write(f"{system_prompt_tutor}\n\n{prompt}")
        
        response = choice.message.parsed
        solution_program = response.program
        
        # if not ON_HEROKU:
        with open(os.path.join(output_path, 'annotations.json'), 'w') as f:
            json.dump(response.dict(), f, indent=4)
        with open(os.path.join(output_path, "program.py"), 'w') as f:
            f.write(solution_program)
            

        print("response.context_relevance=", response.context_relevance)
        if not response.context_relevance:
            context_satisfied = False
            return context_satisfied

    return context_satisfied

def query_simulated_judge(query_path, theme, programming_concepts, task, model_configuration, task_dict):
    model = model_configuration["judge"]["model"]
    num_judges = model_configuration["judge"]["quantity"]
    temp = model_configuration["judge"]["temperature"]
    
    task_path = os.path.join(query_path, task)
    simulated_judges_path = os.path.join(task_path, "simulated_judges")
    os.makedirs(simulated_judges_path, exist_ok=True)

    query_judge(task_path, theme, programming_concepts, task_dict[task]['task_description'], task_dict[task]['test_suite'], model, temp, simulated_judges_path, num_judges)

def parse_simulated_students_responses(generated_tasks_path, task, num_students):
    futures = []

    with open(os.path.join(parent_dir, 'data', 'list_of_llms.json'), 'r') as f: 
        llm_list = json.load(f)
    with open(os.path.join(parent_dir, 'data', 'list_of_temperatures.txt'), 'r') as f: 
        temperatures = f.read().splitlines()

    task_path = os.path.join(generated_tasks_path, task)
    simulated_students_path = os.path.join(task_path, "simulated_students")

    for llm_name, llm_idx in llm_list.items():
        for temp in temperatures:
            for rollout in range(num_students):
                parse_student_response(os.path.join(simulated_students_path, f"{llm_name}_temp-{temp}_{rollout}"))