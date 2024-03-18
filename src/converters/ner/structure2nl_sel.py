import json
import re
from collections import OrderedDict
from typing import List, Union, Dict, Tuple
import numpy as np


from src.converters.structure_converter import StructureConverter
from src.converters.record import EntityRecord, RelationRecord
from src.utils.file_utils import load_yaml,load_schema

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
                 "The named entities in the text: "
                 ]
        prompt.extend(input)

        if prompt_part_only:
            return ''.join(prompt)

        record = record.replace('extra_id_','')

        prompt.append(record)
        return ''.join(prompt) + '\n'


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
        sample:
        {'text': 'CRICKET - LEICESTERSHIRE TAKE OVER AT TOP AFTER INNINGS VICTORY .',
        'tokens': ['CRICKET', '-', 'LEICESTERSHIRE', 'TAKE', 'OVER', 'AT', 'TOP', 'AFTER', 'INNINGS', 'VICTORY', '.'],
        'record': '<extra_id_0> <extra_id_0> organization <extra_id_5> LEICESTERSHIRE <extra_id_1> <extra_id_1>',
        'entity': [{'type': 'organization', 'offset': [2], 'text': 'LEICESTERSHIRE'}],
        'relation': [],
        'event': [],
        'spot': ['organization'],
        'asoc': [],
        'spot_asoc': [{'span': 'LEICESTERSHIRE', 'label': 'organization', 'asoc': []}]}

        code:
        The text is : "CRICKET -
        LEICESTERSHIRE TAKE OVER AT TOP AFTER INNINGS VICTORY .".
        Find named entities such as organization, person,
        miscellaneous, location in the text. The organization
        "LEICESTERSHIRE" exist in the text.
        :param sample:
        :param code:
        :return:
        """
        text = input_dict['text']
        tokens = input_dict['tokens']

        entity = input_dict['entity']
        exist_nested = self.existing_nested(entity)

        sel2record = SEL2Record(
            schema_dict=self.schema_dict,
            decoding_schema=self.decoding,
            map_config=self.map_config,
        )
        pattern = re.compile(r"The named entities in the text:\s*(.*)")

        pred = re.search(pattern, output_str).group(1)
        pred = pred.strip()
        #
        # print ("text: ", text)
        # print ("output_str: ", output_str)
        # print ("pred: ", pred)
        pred_record = sel2record.sel2record(pred, text, tokens)
        pred_record['statistic']['complex'] = exist_nested

        return pred_record


if __name__ == "__main__":
    schema_folder = 'data/conll03'
    map_config_path = 'config/offset_map/first_offset_en.yaml'
    val_path = 'data/conll03/val.json'
    with open(val_path) as fin:
        line = fin.readline()
        line = eval(line.strip())
    data = line
    # print ("dev data:\n", data)

    converter = NLSELPromptCreator(schema_folder=schema_folder,
                                   map_config_path=map_config_path)
    # convert the whole sample
    prompt = converter.structure_to_input(data, prompt_part_only=False)
    print ("prompt:\n", prompt)

    # we have to provide the init state to the sample
    # prompt = converter.generate_sample_head(data)
    # print("sample head: ", prompt)
    # code = """
    # The text is : "CRICKET - LEICESTERSHIRE TAKE OVER AT TOP AFTER INNINGS VICTORY .". The named entities in the text: <extra_id_0> <extra_id_0> organization <extra_id_5> LEICESTERSHIRE <extra_id_1> <extra_id_1>
    # """

    # data = {"text":"Enterprises from domestic coastal provinces and cities increased , and there are altogether 30 enterprise representatives from 30 provinces , cities and autonomous regions coming to this meeting .","tokens":["Enterprises","from","domestic","coastal","provinces","and","cities","increased",",","and","there","are","altogether","30","enterprise","representatives","from","30","provinces",",","cities","and","autonomous","regions","coming","to","this","meeting","."],"entity":[{"type":"geographical social political","offset":[2,3,4,5,6],"text":"domestic coastal provinces and cities"},{"type":"geographical social political","offset":[17,18,19,20,21,22,23],"text":"30 provinces , cities and autonomous regions"},{"type":"organization","offset":[0,1,2,3,4,5,6],"text":"Enterprises from domestic coastal provinces and cities"},{"type":"person","offset":[12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27],"text":"altogether 30 enterprise representatives from 30 provinces , cities and autonomous regions coming to this meeting"}],"relation":[],"event":[],"spot":["person","organization","geographical social political"],"asoc":[],"spot_asoc":[{"span":"Enterprises from domestic coastal provinces and cities","label":"organization","asoc":[]},{"span":"domestic coastal provinces and cities","label":"geographical social political","asoc":[]},{"span":"altogether 30 enterprise representatives from 30 provinces , cities and autonomous regions coming to this meeting","label":"person","asoc":[]},{"span":"30 provinces , cities and autonomous regions","label":"geographical social political","asoc":[]}]}
    # code = r'The text is : "CRICKET - LEICESTERSHIRE TAKE OVER AT TOP AFTER INNINGS VICTORY .". The named entities in the text: <0> <0> organization <5> LEICESTERSHIRE <1> <1>\n'

    code = repr(prompt)
    # conver the prediction to the answers
    predictions = converter.output_to_structure(data, code)
    print (predictions)
