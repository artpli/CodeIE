import argparse
import json
import random
from tqdm import tqdm
import subprocess

from src.converters.ner.structure2pl_func import PLFuncPromptCreator as NERPLFuncPromptCreator
from src.converters.ner.structure2nl_sel import NLSELPromptCreator as NERNLSELPromptCreator

from src.utils.file_utils import load_yaml,load_schema
import pandas as pd

def eval(src_file, pred_file, save_file, job_type,
         schema_path, map_config_path):

    src_d = pd.read_json(src_file, orient='records', lines=True)

    with open(pred_file, 'r') as f:
        pred_d = []
        for line in f:
            data = json.loads(line.strip())
            pred_d.append(data)

    schema = load_schema(schema_path)
    map_config = load_yaml(map_config_path)

    if job_type == 'ner-pl-func':
        converter = NERPLFuncPromptCreator(schema=schema,map_config=map_config)
    elif job_type == 'ner-nl-sel':
        converter = NERNLSELPromptCreator(schema=schema,map_config=map_config)
    else:
        raise NotImplementedError(job_type)

    prediction_list = []
    for qid, src_data in tqdm(src_d.iterrows(), total=len(src_d)):
        pred = pred_d[qid]
        predictions = converter.output_to_structure(src_data, pred['generated_code'])
        prediction_list.append({"entity": predictions,"relation": {"offset": [], "string": []},"event": {"offset": [], "string": []}})
    pd.DataFrame(prediction_list).to_json(save_file, orient='records', lines=True)

def config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_output_file', type=str)
    parser.add_argument('--output_file', type=str)
    parser.add_argument('--src_file', type=str)
    parser.add_argument('--job_type', type=str)
    parser.add_argument("--schema_path", type=str, required=True)
    parser.add_argument("--map_config_path", type=str, required=True)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = config()
    save_file = args.output_file

    eval(args.src_file, args.raw_output_file,
         save_file, args.job_type,
         args.schema_path, args.map_config_path)
