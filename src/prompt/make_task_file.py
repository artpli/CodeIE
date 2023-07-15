import pandas as pd
from tqdm import tqdm
from src.converters.get_converter import ConverterFactory
from src.utils.file_utils import load_yaml, load_schema, read_data

def make_task_file(args):
    data = read_data(args.inpath)
    converter = ConverterFactory.get_converter(args.job_type,schema_folder=args.schema_path, map_config_path=args.map_config_path)

    res = []
    for i, row in tqdm(data.iterrows(), total=len(data)):
        try:
            struct_input = converter.structure_to_input(row, prompt_part_only=False)
            if struct_input is None:
                continue
            tmp = {k: v for (k, v) in row.items() if k not in ['record']}
            tmp["input_idx"] = i
            tmp["input_prompt"] = converter.structure_to_input(row, prompt_part_only=True)
            tmp["reference_output"] = struct_input
        except Exception as e:
            raise e
        res.append(tmp)
    
    # successfully converted
    conversion_rate = len(res) / len(data)
    pd.DataFrame(res).to_json(args.outpath, orient='records', lines=True)
    print(f"Converted {len(res)} out of {len(data)} rows ({conversion_rate:.2%})")
    print ("Saved to ", args.outpath)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--inpath", type=str, required=True)
    parser.add_argument("--outpath", type=str, required=True)
    parser.add_argument("--job_type", type=str, required=True)
    parser.add_argument("--schema_path", type=str, required=True)
    parser.add_argument("--map_config_path", type=str, required=True)
    args = parser.parse_args()

    make_task_file(args)