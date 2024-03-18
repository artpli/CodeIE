import yaml
import pandas as pd

def load_schema(schema_path):
    with open(schema_path,encoding='utf8') as fin:
        entity_line = fin.readline().strip()
        relation_line = fin.readline().strip()
        spot_asoc_line = fin.readline().strip()

    return {'entity_schema': eval(entity_line),
            'relation_schema': eval(relation_line),
            'spot_asoc_schema': eval(spot_asoc_line)}

def load_yaml(yaml_path):
    with open(yaml_path,'r') as fin:
        map_config = yaml.load(fin.read(), Loader=yaml.FullLoader)
    return map_config

def read_data(inpath):
    if "json" in inpath:
        data = pd.read_json(inpath, orient='records', lines=True)
    else:
        raise ValueError(f"Unknown input format: {inpath}")
    return data