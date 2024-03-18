import json
import re
from collections import OrderedDict

from typing import List, Union, Dict, Tuple

from src.converters.structure_converter import StructureConverter
from uie.sel2record.record import MapConfig
from uie.sel2record.sel2record import SEL2Record


class NLSELPromptCreator(StructureConverter):

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
        """
        text = input_dict['text']
        record = input_dict['record']

        prompt = []

        input = ['The text is : ',
                 "\"" + text + "\". ",
                 "The relations of named entities in the text: "
                 ]

        prompt.extend(input)

        if prompt_part_only:
            return ''.join(prompt)

        record = record.replace('extra_id_','')
        prompt.append(record)

        return ''.join(prompt) + '\n'


    def existing_complex_rel(self, relation_dict_list):
        rel_offset = []
        for rel in relation_dict_list:
            temp_args = rel['args']
            off1 = temp_args[0]['offset']
            off2 = temp_args[1]['offset']
            all_off = sorted([off1,off2])

            tmp_offset = all_off[0] + all_off[1]
            rel_offset.append(tmp_offset)

        sorted_offset = sorted(rel_offset)
        start = -1
        end = -1
        for so in sorted_offset:
            temp_s, temp_e = so[0],so[-1]
            if temp_s <= end:
                return True
            start = temp_s
            end = temp_e
        return False

    def output_to_structure(self, input_dict: dict, output_str: str):
        """
        {'text': 'Sun Hung Kai Properties , a Hong Kong construction firm with a 27 percent share ;',
        'tokens': ['Sun', 'Hung', 'Kai', 'Properties', ',', 'a', 'Hong', 'Kong', 'construction', 'firm', 'with', 'a', '27', 'percent', 'share', ';'],
        'record': '<extra_id_0> <extra_id_0> organization <extra_id_5> Sun Hung Kai Properties <extra_id_0> organization in <extra_id_5> Hong Kong <extra_id_1> <extra_id_1> <extra_id_0> location <extra_id_5> Hong Kong <extra_id_1> <extra_id_0> other <extra_id_5> 27 percent <extra_id_1> <extra_id_1>', 'entity': [{'type': 'organization', 'offset': [0, 1, 2, 3],
        'text': 'Sun Hung Kai Properties'}, {'type': 'location', 'offset': [6, 7], 'text': 'Hong Kong'}, {'type': 'other', 'offset': [12, 13], 'text': '27 percent'}],
        'relation': [{'type': 'organization in', 'args': [{'type': 'organization', 'offset': [0, 1, 2, 3], 'text': 'Sun Hung Kai Properties'}, {'type': 'location', 'offset': [6, 7], 'text': 'Hong Kong'}]}],
        'event': [], 'spot': ['organization', 'other', 'location'], 'asoc': ['organization in'], 'spot_asoc': [{'span': 'Sun Hung Kai Properties', 'label': 'organization',
        'asoc': [['organization in', 'Hong Kong']]}, {'span': 'Hong Kong', 'label': 'location', 'asoc': []}, {'span': '27 percent', 'label': 'other', 'asoc': []}]}
        """

        text = input_dict['text']
        tokens = input_dict['tokens']
        relation_dict = input_dict['relation']
        is_complex = self.existing_complex_rel(relation_dict)

        sel2record = SEL2Record(
            schema_dict=self.schema_dict,
            decoding_schema=self.decoding,
            map_config=self.map_config,
        )
        pattern = re.compile(r"The relations of named entities in the text: \s*(.*)")
        pred = re.search(pattern, output_str).group(1)
        pred = pred.strip()

        # print (output_str)
        # print (repr(pred))
        # exit(0)

        pred_record = sel2record.sel2record(pred, text, tokens)
        pred_record['statistic']['complex'] = is_complex
        return pred_record


if __name__ == "__main__":
    schema_folder = 'data/conll04'
    map_config_path = 'config/offset_map/closest_offset_en.yaml'

    val_path = 'data/conll04/val.json'
    with open(val_path) as fin:
        line0 = fin.readline()
        line = fin.readline()
        line = fin.readline()
        line = fin.readline()
        line = eval(line.strip())
    data = line
    print ("dev data:\n", data)

    converter = NLSELPromptCreator(schema_folder=schema_folder,
                                   map_config_path=map_config_path)
    # convert the whole sample
    prompt = converter.structure_to_input(data, prompt_part_only=False)
    print ("prompt:\n", prompt)
    out_string = 'The text is : "Sun Hung Kai Properties , a Hong Kong construction firm with a 27 percent share ;". The relationships of named entities in the text: <extra_id_0> <extra_id_0> organization <extra_id_5> Sun Hung Kai Properties <extra_id_0> organization in <extra_id_5> Hong Kong <extra_id_1> <extra_id_1> <extra_id_0> location <extra_id_5> Hong Kong <extra_id_1> <extra_id_0> other <extra_id_5> 27 percent <extra_id_1> <extra_id_1>'
    out_string = out_string.replace('extra_id_', '')
    results = converter.output_to_structure(data,out_string)
    print (results)
    exit(0)



