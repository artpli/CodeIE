import json
import re
from collections import defaultdict, OrderedDict
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

        goal = 'named entity recognition'
        func_head = self.to_function_head(self.to_function_name(goal),input='input_text')
        prompt.append(func_head)

        docstring = '\t""" extract named entities from the input_text . """'
        prompt.append(docstring)

        input_text = f'\tinput_text = "{text}"'
        prompt.append(input_text)

        entity_list_init = '\tentity_list = []'
        prompt.append(entity_list_init)

        inline_annotation = '\t# extracted named entities'
        prompt.append(inline_annotation)

        if prompt_part_only:
            return self.list_to_str(prompt)

        for sc in spot_asoc_list:
            entity_text = sc['span']
            entity_type = sc['label']
            prompt.append(f'\tentity_list.append({{"text": "{entity_text}", "type": "{entity_type}"}})')

        prompt = self.list_to_str(prompt)
        return prompt + '\n'

    def existing_nested(self, entity_dict_list):
        entity_offset = []
        for ent in entity_dict_list:
            tmp_offset = ent['offset']
            entity_offset.append(tmp_offset)

        sorted_offset = sorted(entity_offset)
        start = -1
        end = -1
        for so in sorted_offset:
            temp_s, temp_e = so[0],so[-1]
            if temp_s <= end:
                return True
            start = temp_s
            end = temp_e
        return False


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
        text = input_dict['text']
        tokens = input_dict['tokens']

        entity = input_dict['entity']
        exist_nested = self.existing_nested(entity)


        sent_records = {}
        sent_records['entity'] = []

        statistic_dict = {}
        statistic_dict['ill-formed'] = False
        statistic_dict['Invalid-Label'] = False
        statistic_dict['Invalid-Text-Span'] = False
        statistic_dict['Invalid-Label-asoc'] = False
        statistic_dict['Invalid-Text-Span-asoc'] =False

        # ill-formed
        if '# extracted named entities' not in output_str:
            print ("error structure 1")
            print(repr(output_str))
            statistic_dict['ill-formed'] = True

        temp_entities = re.findall(r'entity_list.append\((.*?)\)\n', output_str)

        if output_str.endswith("extracted named entities\n") == False and len(temp_entities) == 0:
            print ("error structure 2")
            print(repr(output_str))
            statistic_dict['ill-formed'] = True

        # todo: assert lines = len(temp_entities)
        for te in temp_entities:
            try:
                pattern = '{"text": "(.*?)", "type": "(.*?)"}'
                segments = re.split(pattern, te)
                assert len(segments)==4 and segments[0] == '' and segments[-1] == ''
                if segments[2] not in self.entity_schema:
                    statistic_dict['Invalid-Label'] = True
                    # print ("invalid label: ", segments[2])
                    # exit(0)
                    continue

                if segments[1] =='' or segments[1] not in text:
                    statistic_dict['Invalid-Text-Span'] = True
                    #
                    # print ("Invalid-Text-Span: ", segments[1])
                    # print ("text: ", text)
                    # exit(0)
                    continue

                sent_records['entity'].append({'text': segments[1] , 'type': segments[2]})
                # te = eval(te)
                # sent_records['entity'].append({'text': te['text'] , 'type': te['type']})
            except:
                # print ("*" * 10)
                # print ("error structure 3")
                # print ("tokens: ", tokens)
                # print ("output_str: ", output_str)
                # print ("te: ", te)
                # print ("*" * 10)
                statistic_dict['ill-formed'] = True
                continue

        statistic_dict['complex'] = exist_nested

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
        return {"entity": offset_records,
                "relation": {"offset": [], "string": []},
                "event": {"offset": [], "string": []},
                "statistic": statistic_dict}


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
    # print ('data: ', data)
    # print ('data keys: ', data.keys())


    converter = PLFuncPromptCreator(schema_folder=schema_path,
                                    map_config_path=map_config_path)
    # convert the whole sample
    prompt = converter.structure_to_input(data, prompt_part_only=False)
    # print ("prompt:\n", prompt)
    # code=repr(prompt)
    #
    data = {"text":"Two goals from defensive errors in the last six minutes allowed Japan to come from behind and collect all three points from their opening meeting against Syria .","tokens":["Two","goals","from","defensive","errors","in","the","last","six","minutes","allowed","Japan","to","come","from","behind","and","collect","all","three","points","from","their","opening","meeting","against","Syria","."],"entity":[{"type":"location","offset":[26],"text":"Syria"},{"type":"location","offset":[11],"text":"Japan"}],"relation":[],"event":[],"spot":["location"],"asoc":[],"spot_asoc":[{"span":"Japan","label":"location","asoc":[]},{"span":"Syria","label":"location","asoc":[]}],"input_idx":9,"input_prompt":"def named_entity_extraction(input_text):\n\t\"\"\" extract named entities from the input_text . \"\"\"\n\tinput_text = \"Two goals from defensive errors in the last six minutes allowed Japan to come from behind and collect all three points from their opening meeting against Syria .\"\n\tentity_list = []\n\t# extracted named entities","reference_output":"def named_entity_extraction(input_text):\n\t\"\"\" extract named entities from the input_text . \"\"\"\n\tinput_text = \"Two goals from defensive errors in the last six minutes allowed Japan to come from behind and collect all three points from their opening meeting against Syria .\"\n\tentity_list = []\n\t# extracted named entities\n\tentity_list.append({\"entity_text\": \"Japan\"}, \"entity_type\": \"location\")\n\tentity_list.append({\"entity_text\": \"Syria\"}, \"entity_type\": \"location\")\n"}

    code = r'def named_entity_extraction(input_text):\n\t\"\"\" extract named entities from the input_text . \"\"\"\n\tinput_text = \"Two goals from defensive errors in the last six minutes allowed Japan to come from behind and collect all three points from their opening meeting against Syria .\"\n\tentity_list = []\n\t# extracted named entities\n\tentity_list.append({\"entity_text\": \"Japan\"}, \"entity_type\": \"location\")\n\tentity_list.append({\"entity_text\": \"Syria\"}, \"entity_type\": \"location\")\n'
    # conver the prediction to the answers
    print (data)
    print (code)

    predictions = converter.output_to_structure(data, code)
    print ("output: \n")
    print (predictions)
