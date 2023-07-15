import json
import re
from collections import OrderedDict,defaultdict
from typing import List, Union, Dict, Tuple

from src.converters.structure_converter import StructureConverter
from src.utils.file_utils import load_yaml,load_schema

from uie.sel2record.record import EntityRecord, RelationRecord
from uie.sel2record.record import MapConfig
from uie.sel2record.sel2record import SEL2Record

class PLFuncPromptCreator(StructureConverter):

    def __init__(self, schema_folder=None, map_config_path=None):
        self.schema_dict = SEL2Record.load_schema_dict(schema_folder)
        self.decoding = 'spotasoc'

        record_schema = self.schema_dict['record']
        self.entity_schema = record_schema.type_list
        self.relation_schema = record_schema.role_list
        self.spot_asoc = record_schema.type_role_dict

        self.map_config = MapConfig.load_from_yaml(map_config_path)

    def structure_to_input(self, input_dict: dict, prompt_part_only: bool = False):
        """
        {'text': 'John Wilkes Booth , who assassinated President Lincoln , was an actor .',
        'entity': [{'type': 'people', 'offset': [0, 1, 2], 'text': 'John Wilkes Booth'}, {'type': 'people', 'offset': [6, 7], 'text': 'President Lincoln'}],
        'relation': [{'type': 'kill', 'args': [{'type': 'people', 'offset': [0, 1, 2], 'text': 'John Wilkes Booth'}, {'type': 'people', 'offset': [6, 7], 'text': 'President Lincoln'}]}],
        'spot': ['people'],
        'asoc': ['kill'],
        spot_asoc: {"location": ["located in"],
                    "organization": ["organization in"],
                    "other": [],
                    "people": ["live in", "work for", "kill"]}
        """

        text = input_dict['text']
        entity_list = input_dict['entity']
        relation_list = input_dict['relation']
        spot_list = input_dict['spot']
        asoc_list = input_dict['asoc']

        prompt = []

        goal = 'relation extraction'
        func_head = self.to_function_head(self.to_function_name(goal),input='input_text')
        prompt.append(func_head)

        docstring = '\t""" extract the relationships of named entities from the input_text . """'
        prompt.append(docstring)

        input_text = f'\tinput_text = "{text}"'
        prompt.append(input_text)

        inline_annotation = '\t# extracted relation list'
        prompt.append(inline_annotation)

        if prompt_part_only:
            return self.list_to_str(prompt)

        for asoc in asoc_list:
            for r in relation_list:
                if r['type'] == asoc:
                    arg0, arg1 = r['args']
                    arg0_type, arg0_text = arg0['type'], arg0['text']
                    arg1_type, arg1_text = arg1['type'], arg1['text']
                    arg0_type = '"' + arg0_type + '"'
                    arg0_text = '"' + arg0_text + '"'
                    arg1_type = '"' + arg1_type + '"'
                    arg1_text = '"' + arg1_text + '"'
                    asoc = '"' + asoc + '"'
                    prompt.append(f'\tentities_relation = ({arg0_type}, {arg0_text}, {asoc}, {arg1_type}, {arg1_text})')

        prompt = self.list_to_str(prompt)
        return prompt + '\n'

    def output_to_structure(self, input_dict: dict, output_str: str):
        """
        {'text': 'Sun Hung Kai Properties , a Hong Kong construction firm with a 27 percent share ;',
        'tokens': ['Sun', 'Hung', 'Kai', 'Properties', ',', 'a', 'Hong', 'Kong', 'construction', 'firm', 'with', 'a', '27', 'percent', 'share', ';'],
        'record': '<extra_id_0> <extra_id_0> organization <extra_id_5> Sun Hung Kai Properties <extra_id_0> organization in <extra_id_5> Hong Kong <extra_id_1> <extra_id_1> <extra_id_0> location <extra_id_5> Hong Kong <extra_id_1> <extra_id_0> other <extra_id_5> 27 percent <extra_id_1> <extra_id_1>', 'entity': [{'type': 'organization', 'offset': [0, 1, 2, 3],
        'text': 'Sun Hung Kai Properties'}, {'type': 'location', 'offset': [6, 7], 'text': 'Hong Kong'}, {'type': 'other', 'offset': [12, 13], 'text': '27 percent'}],
        'relation': [{'type': 'organization in', 'args': [{'type': 'organization', 'offset': [0, 1, 2, 3], 'text': 'Sun Hung Kai Properties'}, {'type': 'location', 'offset': [6, 7], 'text': 'Hong Kong'}]}],
        'event': [], 'spot': ['organization', 'other', 'location'], 'asoc': ['organization in'], 'spot_asoc': [{'span': 'Sun Hung Kai Properties', 'label': 'organization',
        'asoc': [['organization in', 'Hong Kong']]}, {'span': 'Hong Kong', 'label': 'location', 'asoc': []}, {'span': '27 percent', 'label': 'other', 'asoc': []}]}

        def relation_extraction(input_text):
	        # extract the relationships of named entities from the input_text .
            input_text = "Sun Hung Kai Properties , a Hong Kong construction firm with a 27 percent share ;"
            # extracted relation list
            entities_relation = ("organization", "Sun Hung Kai Properties", "organization in", "location", "Hong Kong")

        """
        tokens = input_dict['tokens']

        sent_records = {}
        sent_records['relation'] = []

        # ['type': xxx, 'roles': [(type,text),(type,text)]]
        entities_relation_list = re.findall(r'entities_relation = \((.*?)\)', output_str)
        for ent_rel in entities_relation_list:
            temp_entities_relation = ent_rel.split(', ')
            temp_entities_relation = [er.strip(r'\"') for er in temp_entities_relation]
            if len(temp_entities_relation) != 5:
                continue
            temp_entities = [(temp_entities_relation[0],temp_entities_relation[1]),
                             (temp_entities_relation[3],temp_entities_relation[4])]

            sent_records['relation'].append({'type': temp_entities_relation[2], 'roles':temp_entities})

        offset_records = {}

        record_map = RelationRecord(map_config=self.map_config)

        offset_records['offset'] = record_map.to_offset(
            instance=sent_records.get('relation', []),
            tokens=tokens,
        )
        offset_records['string'] = record_map.to_string(
            sent_records.get('relation', []),
        )
        return {"entity": {"offset": [], "string": []},"relation": offset_records,"event": {"offset": [], "string": []}}

if __name__ == "__main__":
    schema_path = 'data/conll04'
    map_config_path = 'config/offset_map/closest_offset_en.yaml'

    val_path = 'data/conll04/val.json'
    with open(val_path) as fin:
        line0 = fin.readline()
        line = fin.readline()
        line = fin.readline()
        line = fin.readline()
        line = eval(line.strip())
    data = line

    converter = PLFuncPromptCreator(schema_folder=schema_path,
                                    map_config_path=map_config_path)

    # convert the whole sample
    prompt = converter.structure_to_input(data,prompt_part_only=False)

    data = {"text":"But the authors suggested that Alekseev , along with others in the Soviet diplomatic corps , were not receiving accurate information from Moscow about the missiles .","tokens":["But","the","authors","suggested","that","Alekseev",",","along","with","others","in","the","Soviet","diplomatic","corps",",","were","not","receiving","accurate","information","from","Moscow","about","the","missiles","."],"entity":[{"type":"people","offset":[5],"text":"Alekseev"},{"type":"location","offset":[12],"text":"Soviet"},{"type":"location","offset":[22],"text":"Moscow"}],"relation":[{"type":"live in","args":[{"type":"people","offset":[5],"text":"Alekseev"},{"type":"location","offset":[12],"text":"Soviet"}]}],"event":[],"spot":["location","people"],"asoc":["live in"],"spot_asoc":[{"span":"Alekseev","label":"people","asoc":[["live in","Soviet"]]},{"span":"Soviet","label":"location","asoc":[]},{"span":"Moscow","label":"location","asoc":[]}]}

    out_string = r'def relation_extraction(input_text):\n\t\"\"\" extract the relationships of named entities from the input_text . \"\"\"\n\tinput_text = \"But the authors suggested that Alekseev , along with others in the Soviet diplomatic corps , were not receiving accurate information from Moscow about the missiles .\"\n\t# extracted relation list\n\tentities_relation = (\"people\", \"Alekseev\", \"receive\", \"information\", \"accurate information\")\n'
    results = converter.output_to_structure(data,out_string)
    print (results)
    exit(0)