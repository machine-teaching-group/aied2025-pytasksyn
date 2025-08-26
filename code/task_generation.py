import os
import json

from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
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
    
class ProgrammingProblem(BaseModel):
    task_description: str
    test_suite: str
    solution_program: str
    
def parse_task(i, response, output_path, theme, concepts):
    task_folder = os.path.join(output_path, f'task_{i}')
    os.makedirs(task_folder, exist_ok=True)

    try:
        if not ON_HEROKU:
            with open(os.path.join(task_folder, 'task_description.txt'), 'w') as f:
                f.write(response.task_description)
        solution_program = response.solution_program.replace('```python', '').replace('```', '')
        test_suite = response.test_suite.replace('```python', '').replace('```', '')

        with open(os.path.join(task_folder, 'solution_program.py'), 'w') as f:
            f.write(solution_program)
        with open(os.path.join(task_folder, 'test_suite.py'), 'w') as f:
            f.write(test_suite)
        with open(os.path.join(task_folder, 'test_solution_results.txt'), 'w') as f:
            f.write(json.dumps({}, indent=4))
    except Exception as e:
        print(f"Failed to parse the response for task {i}.")
        print(e)
        raise Exception(f"Failed to parse the response for task {i}.")
    return f'task_{i}', response.task_description, solution_program, test_suite

def gen_tasks(query_path, theme, programming_concepts, num_tasks_per_pair, model_configuration):
    # task_dict = {}
    prompt = user_prompt_expert.format(theme=theme, concepts= str(programming_concepts))
    print(prompt)
   
    ### Query the model
    model = model_configuration["expert"]["model"]
    completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {   
                            "role": "system", "content": system_prompt_expert,
                            "role": "user", "content": prompt
                        }
                    ],
                    response_format=ProgrammingProblem,
                    n=num_tasks_per_pair)
    
    responses = [completion.choices[i].message.parsed for i in range(num_tasks_per_pair)]
    if not ON_HEROKU:
        ### Save the prompt to a file
        with open(os.path.join(query_path, 'prompt.txt'), 'w') as f:
            f.write(system_prompt_expert)
            f.write("\n\n")
            f.write(prompt)

        ### Save completion and token count to files
        with open(os.path.join(query_path, 'responses.txt'), 'w') as f:
            f.write(str([completion.choices[i].message for i in range(num_tasks_per_pair)]))
        with open(os.path.join(query_path, 'token_count.json'), 'w') as f:
            token_count = completion.usage.to_dict()
            json.dump(token_count, f, indent=4)

    return responses