import argparse
import json
import random
from tqdm import tqdm
import subprocess
from src.converters.get_converter import ConverterFactory

import pandas as pd

def eval(src_file, pred_file, save_file, job_type,
         schema_path, map_config_path, pred_key='generated_code'):

    src_d = pd.read_json(src_file, orient='records', lines=True)

    with open(pred_file, 'r') as f:
        pred_d = []
        for line in f:
            data = json.loads(line.strip())
            pred_d.append(data)

    converter = ConverterFactory.get_converter(job_type=job_type, schema_folder=schema_path, map_config_path=map_config_path)

    prediction_list = []
    ill_formed = 0
    invalid_label = 0
    invalid_text_span = 0
    invalid_label_asoc = 0
    invalid_text_span_asoc = 0

    for qid, src_data in tqdm(src_d.iterrows(), total=len(src_d)):
        pred = pred_d[qid]
        predictions = converter.output_to_structure(src_data, pred[pred_key])

        if predictions['statistic']['ill-formed'] == True:
            ill_formed += 1
        if predictions['statistic']['Invalid-Label'] == True:
            invalid_label += 1
        if predictions['statistic']['Invalid-Text-Span'] == True:
            invalid_text_span += 1
        if predictions['statistic']['Invalid-Label-asoc'] == True:
            invalid_label_asoc += 1
        if predictions['statistic']['Invalid-Text-Span-asoc'] == True:
            invalid_text_span_asoc += 1

        prediction_list.append(predictions)
    pd.DataFrame(prediction_list).to_json(save_file, orient='records', lines=True)
    print ("ill_formed number: ", ill_formed)
    print ("Invalid-Label number: ", invalid_label)
    print ("Invalid-Text-Span number: ", invalid_text_span)
    print ("Invalid-Label-asoc number: ", invalid_label_asoc)
    print ("Invalid-Text-Span-asoc number: ", invalid_text_span_asoc)


def config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw_output_file', type=str)
    parser.add_argument('--output_file', type=str)
    parser.add_argument('--src_file', type=str)
    parser.add_argument('--job_type', type=str)
    parser.add_argument("--schema_path", type=str, required=True)
    parser.add_argument("--map_config_path", type=str, required=True)
    parser.add_argument("--pred_key", type=str, default='generated_code')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = config()
    save_file = args.output_file

    eval(args.src_file, args.raw_output_file,
         save_file, args.job_type,
         args.schema_path, args.map_config_path, args.pred_key)
