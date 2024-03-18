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
        spot_asoc_list = input_dict['spot_asoc']
        prompt = []

        goal = 'relation extraction'
        func_head = self.to_function_head(self.to_function_name(goal),input='input_text')
        prompt.append(func_head)

        docstring = '\t""" extract the relations of named entities from the input_text . """'
        prompt.append(docstring)

        input_text = f'\tinput_text = "{text}"'
        prompt.append(input_text)

        entity_relation_list_init = '\tentity_relation_list = []'
        prompt.append(entity_relation_list_init)

        inline_annotation = '\t# extracted relations'
        prompt.append(inline_annotation)

        if prompt_part_only:
            return self.list_to_str(prompt)

        ent2type = defaultdict(dict)
        for tmp_e in entity_list:
            ent2type[tmp_e['text']] = tmp_e['type']

        # [{"span": "VC", "label": "method", "asoc": []},
        # {"span": "it", "label": "generic", "asoc": []},
        # {"span": "devices", "label": "generic", "asoc": [["used for", "it"]]},
        # {"span": "sufficient computational resources", "label": "material", "asoc": [["feature of", "devices"]]}]
        for asoc in spot_asoc_list:
            tmp_start = asoc['span']
            start_type = asoc['label']
            if asoc['asoc'] != []:
                for as_list in asoc['asoc']:
                    tmp_rel = as_list[0]
                    tmp_end = as_list[1]
                    end_type = ent2type[tmp_end]
                    temp_prompt = f'\tentity_relation_list.append({{"rel_type": "{tmp_rel}", "ent1_type": "{start_type}", "ent1_text": "{tmp_start}", "ent2_type": "{end_type}", "ent2_text": "{tmp_end}"}})'
                    prompt.append(temp_prompt)
        prompt = self.list_to_str(prompt)
        return prompt + '\n'

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

        def relation_extraction(input_text):
	        # extract the relationships of named entities from the input_text .
            input_text = "Sun Hung Kai Properties , a Hong Kong construction firm with a 27 percent share ;"
            # extracted relation list
            entities_relation = ("organization", "Sun Hung Kai Properties", "organization in", "location", "Hong Kong")

        """

        text = input_dict['text']
        tokens = input_dict['tokens']

        sent_records = {}
        sent_records['relation'] = []

        statistic_dict = {}
        statistic_dict['ill-formed'] = False
        statistic_dict['Invalid-Label'] = False
        statistic_dict['Invalid-Text-Span'] = False
        statistic_dict['Invalid-Label-asoc'] = False
        statistic_dict['Invalid-Text-Span-asoc'] =False

        error_structure = False
        if '# extracted relations' not in output_str:
            print ("error structure 1")
            print(repr(output_str))
            statistic_dict['ill-formed'] = True

        # ['type': xxx, 'roles': [(type,text),(type,text)]]
        entities_relation_list = re.findall(r'entity_relation_list.append\((.+?)\)\n', output_str)

        if output_str.endswith("extracted relations\n") == False and len(entities_relation_list) == 0:
            print ("error structure 2")
            print(repr(output_str))
            statistic_dict['ill-formed'] = True

        # todo: check lines
        for ent_rel in entities_relation_list:
            try:
                temp_entities_relation = eval(ent_rel)
                if len(temp_entities_relation.keys()) != 5:
                    print ("error structure length")
                    print (tokens)
                    print (ent_rel)
                    statistic_dict['ill-formed'] = True
                    continue

                temp_entities = [(temp_entities_relation['ent1_type'],temp_entities_relation['ent1_text']),
                                 (temp_entities_relation['ent2_type'],temp_entities_relation['ent2_text'])]

                if temp_entities_relation['ent1_type'] not in self.entity_schema:
                    statistic_dict['Invalid-Label'] = True
                    continue

                if temp_entities_relation['ent2_type'] not in self.entity_schema:
                    statistic_dict['Invalid-Label'] = True
                    continue

                if temp_entities_relation['ent1_text'] == '' or temp_entities_relation['ent1_text'] not in text:
                    statistic_dict['Invalid-Text-Span'] = True
                    continue

                if temp_entities_relation['rel_type'] not in self.relation_schema:
                    statistic_dict['Invalid-Label-asoc'] = True
                    print ("error rel: ", temp_entities_relation['rel_type'])
                    exit(0)
                    continue

                if temp_entities_relation['ent2_text'] == '' or temp_entities_relation['ent2_text'] not in text:
                    statistic_dict['Invalid-Text-Span-asoc'] = True
                    continue

                sent_records['relation'].append({'type': temp_entities_relation['rel_type'], 'roles':temp_entities})
            except:
                print ("*" * 10)
                print ("error structure 3")
                print (tokens)
                print (ent_rel)
                print ("te: ", ent_rel)
                print ("*" * 10)
                statistic_dict['ill-formed'] = True
                continue

        relation_dict = input_dict['relation']
        is_complex = self.existing_complex_rel(relation_dict)
        statistic_dict['complex'] = is_complex

        offset_records = {}

        record_map = RelationRecord(map_config=self.map_config)

        offset_records['offset'] = record_map.to_offset(
            instance=sent_records.get('relation', []),
            tokens=tokens,
        )
        offset_records['string'] = record_map.to_string(
            sent_records.get('relation', []),
        )
        return {"entity": {"offset": [], "string": []},
                "relation": offset_records,
                "event": {"offset": [], "string": []},
                "statistic": statistic_dict}

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

    prompt = converter.structure_to_input(data,prompt_part_only=False)
    print (prompt)

    # data = {"text":"But the authors suggested that Alekseev , along with others in the Soviet diplomatic corps , were not receiving accurate information from Moscow about the missiles .","tokens":["But","the","authors","suggested","that","Alekseev",",","along","with","others","in","the","Soviet","diplomatic","corps",",","were","not","receiving","accurate","information","from","Moscow","about","the","missiles","."],"entity":[{"type":"people","offset":[5],"text":"Alekseev"},{"type":"location","offset":[12],"text":"Soviet"},{"type":"location","offset":[22],"text":"Moscow"}],"relation":[{"type":"live in","args":[{"type":"people","offset":[5],"text":"Alekseev"},{"type":"location","offset":[12],"text":"Soviet"}]}],"event":[],"spot":["location","people"],"asoc":["live in"],"spot_asoc":[{"span":"Alekseev","label":"people","asoc":[["live in","Soviet"]]},{"span":"Soviet","label":"location","asoc":[]},{"span":"Moscow","label":"location","asoc":[]}]}
    # out_string = r'def relation_extraction(input_text):\n\t\"\"\" extract the relationships of named entities from the input_text . \"\"\"\n\tinput_text = \"But the authors suggested that Alekseev , along with others in the Soviet diplomatic corps , were not receiving accurate information from Moscow about the missiles .\"\n\t# extracted relation list\n\tentities_relation = (\"people\", \"Alekseev\", \"receive\", \"information\", \"accurate information\")\n'
    #
    out_string = repr(prompt)

    results = converter.output_to_structure(data,out_string)


    print (results)
    exit(0)