# [AIED 2025] Synthesizing High-Quality Programming Tasks with LLM-Based Expert and Student Agents

This repository contains the implementation of this paper: [Synthesizing High-Quality Programming Tasks with LLM-Based Expert and Student Agents](https://link.springer.com/chapter/10.1007/978-3-031-98414-3_6).


----------------------------------------
### Overview

The repository has the following structure:
* `code/`: this folder contains files required for the evaluation of our method PyTaskSyn.
* `data/`: this folder contains data necessary for the evaluation.
* `outputs/`: this folder contains outputs from our method.
* `plots/`: this folder contains plots generated for our research questions.

Required packages can be installed by running `pip install -r requirements.txt`.


### Set environment variables
```
export OPENAI_API_KEY=<Your-API-key>
```

### Synthesize tasks from PyTaskSyn
```
python -m code.main\
    --num_themes 5\
    --num_concept_lists_per_theme 5\
    --num_tasks_per_pair 10\
    --output_path outputs
```

### Research questions
```
python -m code.main_results_RQ1

python -m code.main_results_RQ2

python -m code.main_results_RQ3
```

### User studies
```
python -m code.user_study_source_comparison

python -m code.user_study_app_performance
```

### Citation

If you use this code or methodology in your research, please cite our paper:

```bibtex
@InProceedings{Nguyen2025PyTaskSyn,
    author="Nguyen, Manh Hung and P{\u{a}}durean, Victor-Alexandru and Gotovos, Alkis and Tschiatschek, Sebastian and Singla, Adish",
    editor="Cristea, Alexandra I. and Walker, Erin and Lu, Yu and Santos, Olga C. and Isotani, Seiji",
    title="Synthesizing High-Quality Programming Tasks with LLM-Based Expert and Student Agents",
    booktitle="Artificial Intelligence in Education",
    year="2025",
    publisher="Springer Nature Switzerland",
    address="Cham",
    pages="77--91"
}
```
