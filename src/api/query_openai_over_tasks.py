"""
Given a prompt file and path to a task file with the following fields:

1. input_prompt: the code used to prompt codex
2. reference_code: expected completed code
3. reference_graph: expected graph

Runs inference over codex for each input_prompt, and adds the following fields to the output file:

4. generated_code: generated code
5. generated_graph: generated graph

The file can contain other metadata, but the fields above are required.
"""

import os
import sys

sys.path.append(os.getcwd())

from datetime import datetime
import shutil
import time
import openai
import pandas as pd
from tqdm import tqdm
import logging
import os
import pickle

from src.converters.structure_converter import StructureConverter
from src.converters.get_converter import ConverterFactory
from openai_api_wrapper import OpenaiAPIWrapper
from src.prompt.constants import END

from src.utils.file_utils import load_yaml,load_schema

logging.basicConfig(level=logging.INFO)


def run(task_file_path: str,
        num_tasks: int,
        start_idx: int,
        output_file_path: str,
        prompt_path: str,
        keep_writing_output: bool,
        engine: str,
        max_tokens:int, 
        max_requests_per_min: int,
        schema_path:str,
        map_config_path:str,
        start_cut_num:int):
    tasks = pd.read_json(task_file_path, orient='records', lines=True)

    converter = ConverterFactory.get_converter(args.job_type,schema_folder=schema_path, map_config_path=map_config_path)

    if num_tasks != -1:
        tasks = tasks.iloc[start_idx: start_idx+num_tasks]

    fixed_prompt_text = read_prompt(prompt_path)

    results = []

    cache = load_cache(output_file_path)

    num_requests = 0
    time_begin = time.time()

    failed_list = []
    max_failed_time = 10
    max_failed_taskes = 10
    for task_idx, task in tqdm(tasks.iterrows(), total=len(tasks)):
        is_success = False
        tmp_failed_time = 0
        while is_success is False and tmp_failed_time < max_failed_time:
            cut_prompt_examples_list = [None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            cut_prompt_examples_list = cut_prompt_examples_list[start_cut_num:]

            for cut_prompt_examples in cut_prompt_examples_list:
                try:
                    num_requests += 1
                    request_per_minute = maintain_request_per_minute(
                        num_requests=num_requests, time_begin=time_begin,
                        max_requests_per_min=max_requests_per_min, task_idx=task_idx)
                    logging.info("\n")
                    logging.info(
                        f"Task {task_idx} > request/minute = {request_per_minute:.2f}")
                    task_results = run_task(task=task, fixed_prompt_text=fixed_prompt_text,
                                            cache=cache, converter=converter,
                                            cut_prompt_examples=cut_prompt_examples, task_idx=task_idx,
                                            engine=engine, max_tokens=max_tokens)
                    task_results['id'] = task_idx
                    results.append(task_results)
                    is_success = True
                    break
                except openai.error.InvalidRequestError as e:
                    logging.info(
                        f"InvalidRequestError: {e}, trying with shorter prompt (cut_prompt_examples={cut_prompt_examples + 1 if cut_prompt_examples is not None else 1})")
                    # sleep for a bit to further avoid rate limit exceeded exceptions
                    if cut_prompt_examples != cut_prompt_examples_list[-1]:
                        time.sleep(5)
                        continue
                    else:
                        tmp_failed_time = max_failed_time
                        logging.info(f"Failed too many times: {tmp_failed_time}")
                except Exception as e:  # something else went wrong
                    logging.info(f"Task {task_idx} failed: {e}")
                    tmp_failed_time += 1
                    time.sleep(5 * tmp_failed_time)
                    logging.info(f"Restart task {task_idx}")
                    break
            if is_success and keep_writing_output:
                pd.DataFrame(results).to_json(
                    output_file_path, orient='records', lines=True)
        if is_success == False:
            failed_list.append(task_idx)
            logging.info(f"Task {task_idx} failed {max_failed_time} times, skipped and recorded.")
            if failed_list != []:
                print ("failed list:\n", failed_list)
                if len(failed_list) > max_failed_taskes:
                    print ("too many failed taskes. exit().")
                    exit(0)

    print(
        f"Ran {len(results)} out of {len(tasks)} tasks ({len(results) / len(tasks):.2%})")
    pd.DataFrame(results).to_json(
        output_file_path, orient='records', lines=True)
    if failed_list != []:
        print ("failed list:\n", failed_list)
        output_path = output_file_path.rstrip('.jsonl') + '_failed_list.pkl'
        with open(output_path,"w") as fout:
            pickle.dump(failed_list,fout)
        print ("failed list saved into: ", output_path)

def run_task(task: dict, fixed_prompt_text: str, cache: dict,
             converter: StructureConverter, task_idx: int, engine: str,
             max_tokens: int, cut_prompt_examples: int = None) -> dict:
    """Runs the task, and returns the results.

    Args:
        task (dict): The task input
        fixed_prompt_text (str): Used for cases where the input prompt is fixed
        cache (dict): cache of previous results
        converter (GraphPythonConverter): A graph-python converter to parse results
        cut_prompt_examples (int, optional): If provided, the first `cut_prompt_examples` examples are 
                                             deleted. Prevents 4096 errors. Defaults to None.

    Returns:
        dict: A dictionary with the results.
    """
    start_time = time.time()
    prompt_text = fixed_prompt_text if fixed_prompt_text is not None else task['prompt']

    if cut_prompt_examples is not None:
        prompt_text_parts = prompt_text.split(END)
        prompt_text = END.join(prompt_text_parts[cut_prompt_examples:])

    if task['input_prompt'] in cache:
        logging.info(
            f"Task {task_idx} > Using cached result for {task['input_prompt']}")
        codex_response = cache[task['input_prompt']]["codex_response"]
    else:
        codex_response = query_codex(task, prompt_text, engine, max_tokens=max_tokens)

    completed_code = get_completed_code(task, codex_response)

    task_results = {k: v for (k, v) in task.items()}
    task_results["codex_response"] = codex_response
    task_results["generated_code"] = completed_code

    task_results["elapsed_time"] = time.time() - start_time

    return task_results


def maintain_request_per_minute(num_requests: int, time_begin: float, max_requests_per_min: int, task_idx: int) -> float:
    request_per_minute = get_request_per_minute(num_requests, time_begin)
    logging.info("\n")
    while request_per_minute > max_requests_per_min:
        logging.info(
            f"Task {task_idx} > Sleeping! (Requests/minute = {request_per_minute:.2f} > {max_requests_per_min:.2f})")
        time.sleep(1)
        request_per_minute = get_request_per_minute(
            num_requests, time_begin)
    return request_per_minute


def read_prompt(prompt_path):
    if prompt_path is None:
        return None
    with open(prompt_path, "r") as f:
        prompt = f.read()
    return prompt


def load_cache(output_file_path: str):
    """We don't want to query codex repeatedly for the same input. If an output file exists, this
    function creates a "cache" of the results.
    The cache is implemented as a hashmap keyed by `input_prompt`, and maps to the
    entire output entry

    Args:
        output_file_path (str): _description_
    """
    if not os.path.exists(output_file_path):
        return {}
    else:
        # make a backup of the file already there
        shutil.copyfile(output_file_path, output_file_path + "_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        shutil.copy(output_file_path, output_file_path + ".bak")
        cache_data = pd.read_json(
            output_file_path, orient='records', lines=True)
        cache = {row['input_prompt']: row.to_dict()
                 for _, row in cache_data.iterrows()}
        return cache


def query_codex(task: dict, prompt_text: str, engine: str, max_tokens: int):
    prompt = f"{prompt_text} {task['input_prompt']}"
    response = OpenaiAPIWrapper.call(
        prompt=prompt, max_tokens=max_tokens, engine=engine)
    return response


def get_completed_code(task: dict, codex_response: dict) -> str:
    completed_code = OpenaiAPIWrapper.parse_response(codex_response)
    all_code = f"{task['input_prompt']}{completed_code}"
    # NOTE: space is already taken care of, no need to add it again, otherwise indentation will be off
    return all_code


def get_request_per_minute(num_request: int, begin_time: float) -> float:
    elapsed_time = time.time() - begin_time
    request_per_minute = (num_request / elapsed_time) * 60
    return request_per_minute


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task_file_path", type=str, required=True)
    parser.add_argument("--num_tasks", type=int, required=True)
    parser.add_argument("--start_idx", type=int, required=True)
    parser.add_argument("--output_file_path", type=str, required=True)
    parser.add_argument("--prompt_path", type=str,
                        required=False, default=None)
    parser.add_argument("--job_type", type=str, required=True,
                        choices=ConverterFactory.supported_converters)
    parser.add_argument("--keep_writing_output",
                        action="store_true", default=True)
    parser.add_argument("--engine", type=str, required=True)
    parser.add_argument("--max_requests_per_min", type=int, default=10)
    parser.add_argument("--max_tokens", type=int, default=280)
    parser.add_argument("--schema_path", type=str, required=True)
    parser.add_argument("--map_config_path", type=str, required=True)
    parser.add_argument("--start_cut_num", type=int, default=0)
    args = parser.parse_args()

    run(task_file_path=args.task_file_path, num_tasks=args.num_tasks,start_idx=args.start_idx,
        output_file_path=args.output_file_path, prompt_path=args.prompt_path,
        keep_writing_output=args.keep_writing_output, engine=args.engine,
        max_requests_per_min=args.max_requests_per_min,
        max_tokens=args.max_tokens,schema_path=args.schema_path,
        map_config_path=args.map_config_path,start_cut_num=args.start_cut_num)


