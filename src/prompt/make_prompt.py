import pandas as pd
import os
import shutil
import random
import argparse
from collections import defaultdict
import json
import sys

from src.prompt.constants import END
from src.utils.record_schema import RecordSchema

def make_prompt(file_path: str, out_file, n_examples, seed: int = 0):
    random.seed(seed)
    data = [json.loads(line.strip()) for line in open(file_path)]
    if n_examples != -1:
        samples = random.sample(data, n_examples)
    else:
        samples = data
    random.shuffle(samples)

    prompt = ""

    for sample in samples:
        prompt += sample["reference_output"]
        prompt += f"{END}\n\n"

    with open(out_file,'w',encoding='utf-8') as fout:
        fout.write(prompt)
    print ("saved prompt to ", out_file)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', help='Source File Name', required=True)
    parser.add_argument('-tgt', help='Target File Name, n shot sampled',
                        required=True)
    parser.add_argument('-schema_file', help='schema_file', required=True)
    parser.add_argument('-task', help='N-Shot Task name', required=True,
                        choices=['entity', 'relation', 'event'])
    parser.add_argument('-n_examples', help='n_examples',type=int)
    parser.add_argument('-seed', help='Default is None, no random')
    parser.add_argument('-min_len', dest='min_len', help='Default is None', type=int)
    options = parser.parse_args()

    source_file = options.src
    target_file = options.tgt

    make_prompt(file_path=source_file, out_file=target_file, n_examples=options.n_examples)


if __name__ == "__main__":
    main()