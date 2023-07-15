import json
import re
from collections import OrderedDict
from typing import List, Union, Dict, Tuple

from src.converters.structure_converter import StructureConverter
from src.utils.file_utils import load_yaml,load_schema

from uie.sel2record.record import EntityRecord, RelationRecord
from uie.sel2record.record import MapConfig
from uie.sel2record.sel2record import SEL2Record

"""
def extract_named_entity(input_text):   
    # extract named entities from the input_text .

    input_text = "Steve became CEO of Apple in 1998"
    # extracted named entities
    person = ["Steve"]
    organization = ["Apple"]
    person = ["Steve"]
    organization = ["Apple"]    
"""

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
        {'text': 'CRICKET - LEICESTERSHIRE TAKE OVER AT TOP AFTER INNINGS VICTORY .',
        'entity': [{'type': 'organization', 'offset': [2], 'text': 'LEICESTERSHIRE'}],
        'spot': ['organization'],
        "spot_asoc":[{"span":"Japan","label":"location","asoc":[]},{"span":"Syria","label":"location","asoc":[]}]
        """
        text = input_dict['text']
        spot_asoc_list = input_dict['spot_asoc']

        prompt = []

        goal = 'named entity extraction'
        func_head = self.to_function_head(self.to_function_name(goal),input='input_text')
        prompt.append(func_head)

        docstring = '\t""" extract named entities from the input_text . """'
        prompt.append(docstring)

        input_text = f'\tinput_text = "{text}"'
        prompt.append(input_text)

        inline_annotation = '\t# extracted named entities'
        prompt.append(inline_annotation)

        if prompt_part_only:
            return self.list_to_str(prompt)

        for sc in spot_asoc_list:
            entity_text = sc['span']
            entity_type = self.to_function_name(sc['label'])
            prompt.append(f'\t{entity_type} = [ {entity_text} ]')

        prompt = self.list_to_str(prompt)
        return prompt + '\n'

    def output_to_structure(self, input_dict, output_str):
        """
        input_dict:
        {'text': 'West Indian all-rounder Phil Simmons took four for 38 on Friday as Leicestershire beat Somerset by an innings and 39 runs in two days to take over at the head of the county championship .',
        'tokens': ['West', 'Indian', 'all-rounder', 'Phil', 'Simmons', 'took', 'four', 'for', '38', 'on', 'Friday', 'as', 'Leicestershire', 'beat', 'Somerset', 'by', 'an', 'innings', 'and', '39', 'runs', 'in', 'two', 'days', 'to', 'take', 'over', 'at', 'the', 'head', 'of', 'the', 'county', 'championship', '.'],
        'record': '<extra_id_0> <extra_id_0> miscellaneous <extra_id_5> West Indian <extra_id_1> <extra_id_0> person <extra_id_5> Phil Simmons <extra_id_1> <extra_id_0> organization <extra_id_5> Leicestershire <extra_id_1> <extra_id_0> organization <extra_id_5> Somerset <extra_id_1> <extra_id_1>',
        'entity': [{'type': 'organization', 'offset': [12], 'text': 'Leicestershire'}, {'type': 'person', 'offset': [3, 4], 'text': 'Phil Simmons'}, {'type': 'organization', 'offset': [14], 'text': 'Somerset'}, {'type': 'miscellaneous', 'offset': [0, 1], 'text': 'West Indian'}],
        'relation': [], 'event': [], 'spot': ['person', 'organization', 'miscellaneous'], 'asoc': [],
        'spot_asoc': [{'span': 'West Indian', 'label': 'miscellaneous', 'asoc': []}, {'span': 'Phil Simmons', 'label': 'person', 'asoc': []}, {'span': 'Leicestershire', 'label': 'organization', 'asoc': []}, {'span': 'Somerset', 'label': 'organization', 'asoc': []}]}

        output_str:
        def extract_named_entity(input_text):
	        # extract named entities from the input_text.
	        input_text = "West Indian all-rounder Phil Simmons took four for 38 on Friday as Leicestershire beat Somerset by an innings and 39 runs in two days to take over at the head of the county championship ."
            # extracted named entity list
            person_list = ["Phil Simmons"]
            organization_list = ["Leicestershire", "Somerset"]
            miscellaneous_list = ["West Indian"]

        :return:
        """
        tokens = input_dict['tokens']

        sent_records = {}
        sent_records['entity'] = []
        for entity_s in self.entity_schema:
            temp_entities = re.findall(f'{self.to_function_name(entity_s)}' + r' = \[(.*?)\]', output_str)
            if len(temp_entities) != 0:
                temp_entity_list = [
                    {'text': e.strip(), 'type': entity_s} for e in temp_entities
                ]
                sent_records['entity'].extend(temp_entity_list)

        offset_records = {}
        record_map = EntityRecord(map_config=self.map_config)

        offset_records['offset'] = record_map.to_offset(
            instance=sent_records.get('entity', []),
            tokens=tokens,
        )
        offset_records['string'] = record_map.to_string(
            sent_records.get('entity', []),
        )
        """
        {'offset': [('opinion', (10,)), ('aspect', (11, 12)), ('opinion', (32,)), ('aspect', (34,))], 
        'string': [('opinion', 'soft'), ('aspect', 'rubber enclosure'), ('opinion', 'break'), ('aspect', 'seal')]}
        """
        return {"entity": offset_records,"relation": {"offset": [], "string": []},"event": {"offset": [], "string": []}}


if __name__ == "__main__":
    schema_path = 'data/conll03'
    map_config_path = 'config/offset_map/first_offset_en.yaml'

    val_path = 'data/conll03/val.json'
    with open(val_path) as fin:
        line0 = fin.readline()
        line1 = fin.readline()
        line = fin.readline()
        line = eval(line.strip())
    data = line
    print ('data: ', data)
    print ('data keys: ', data.keys())


    converter = PLFuncPromptCreator(schema_folder=schema_path,
                                    map_config_path=map_config_path)
    # convert the whole sample
    prompt = converter.structure_to_input(data, prompt_part_only=False)
    print ("prompt:\n", prompt)

    code = repr(prompt)

    # conver the prediction to the answers
    predictions = converter.output_to_structure(data, code)
    print ("output: \n")
    print (predictions)
