# CodeIE

This is the official repository for "[CodeIE: Large Code Generation Models are Better Few-Shot Information Extractors](https://arxiv.org/abs/2305.05711)" (ACL 2023).    

If you have any questions or suggestions, please feel free to open issues or email Peng Li (lip21 [at] m.fudan.edu.cn). 

## Introduction

Our codebase is mainly modified from the [UIE](https://github.com/universal-ie/UIE) and [CoCoGen](https://github.com/reasoning-machines/CoCoGen) repositories.
We obtained and processed the original NER and RE datasets according to UIE's workflow.
Then we implemented the inference logic of CodeIE referring to CoCoGen's workflow.
Finally we evaluated the model outputs based on UIE's evaluation process.

We sincerely thank these two works and previous works.

## Notice
1. A piece of not-so-good news is that the `Codex` models are now [deprecated by OpenAI](https://platform.openai.com/docs/guides/code), which will have a significant impact on replicating this paper. Some possible solutions include applying for OpenAI's [Researcher Access Program](https://openai.com/form/researcher-access-program) or accessing Codex on [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/work-with-code).
2. Since we are using the closed-source APIs of OpenAI, we are unaware of the technical details behind them, such as the specific pre-training corpora used. Therefore, there might be potential issues of [data contamination](https://hitz-zentroa.github.io/lm-contamination/blog/) in the evaluation of our paper. (Acknowledgement: [Oscar Sainz](https://osainz59.github.io/))

##  Folder Structure
After the following workflow, the final structure of the CodeIE folder will be like this:

```
UIE/ # https://github.com/universal-ie/UIE
CoCoGen/ # https://github.com/reasoning-machines/CoCoGen
CodeIE/ 
│
├── config/ # from UIE
│ ├── data_conf/
│ ├── exp_conf/
│ └── offset_conf/
├── data/ # processed datasets as UIE
│ ├── conll03/
│ ├── conll03_shot/
│ ├── ...
├── processed_data/ # inputs of CodeIE
│ ├── conll03_shot/
│ ├── ...
├── outputs/ # outputs of CodeIE
│ ├── conll03_shot/
│ ├── ...
├── scripts/
│ ├── evaluate_shot.sh
│ ├── make_prompts_shot.sh
│ ├── make_task_files_shot.sh
│ └── query_api_shot.sh
├── src/
└── uie/ # modified from UIE
```

## End-to-End workflow
### Requirements
We first created the conda environment `codeie` and installed related libraries according to the UIE's `Requirements` section.
Then we installed required libraries with the CoCoGen's `requirements.txt` file.

The pipeline looks like this:

```
cd ..
git clone git@github.com:universal-ie/UIE.git
cd UIE

conda create -n codeie python=3.8
pip install torch==1.8.0+cu111 torchvision==0.9.0+cu111 torchaudio==0.8.0 -f https://download.pytorch.org/whl/torch_stable.html
pip install -r requirements.txt

cd ..
git clone git@github.com:reasoning-machines/CoCoGen.git
cd CoCoGen
pip install -r requirements.txt
```

Please note that the version of the `openai` library used by CoCoGen is `0.11.0`. Using the latest OpenAI's library may lead to version incompatibility issues.

### Datasets and Preprocessing
Please refer to the `Datasets of Extraction Tasks` section of UIE's repository to get and preprocess the NER and RE datasets.

When sampling few-shot samples, we viewed `null output` as one special class and sampled corresponding few-shot examples. We provided our new `sample_data_shot.py` file.

Then you can get the `data` folder.

### Models
In order to access OpenAI's `text-davinci-002` and `code-davinci-002` models, you need an OpenAI key and export it with the environment variable `OPENAI_API_KEY`.

You can edit the following line in the `scripts/query_api_shot.sh` file.
```
export OPENAI_API_KEY="" #<YOUR OPENAI KEY>
```

### Inference

- Make task files

Wrap each preprocessed sample with code or natural language prompt. Please read the bash file to gain more information and edit the file to change the config.

```
bash scripts/make_task_files.sh
```

After this process, you will get the `{split}_shot{shot_num}_seed{seed_num}.json` files in the `processed_data/{dataset_name}_shot/{style}/{method}/{tag}` folder. Each line in each file will look like the following sample:

```json
{
    "text":"...",
    "tokens":[...],
    "entity":[
        {"type":"...","offset":[...],"text":"..."},
        {"type":"...","offset":[...],"text":"..."},
        ...
        ],
    "relation":[],
    "event":[],
    "spot":["person","organization","miscellaneous","location"],
    "asoc":[],
    "spot_asoc":[
        {"span":"...","label":"...","asoc":[]},
        {"span":"...","label":"...","asoc":[]},
        ...
        ],
    "input_idx":0,
    "input_prompt":"def named_entity_recognition(input_text):\n\t\"\"\" extract named entities from the input_text . \"\"\"\n\tinput_text = \"...\"\n\tentity_list = []\n\t# extracted named entities",
    "reference_output":"def named_entity_recognition(input_text):\n\t\"\"\" extract named entities from the input_text . \"\"\"\n\tinput_text = \"...\"\n\tentity_list = []\n\t# extracted named entities\n\tentity_list.append({\"text\": \"...\", \"type\": \"...\"})\n\tentity_list.append(..."
}
```


- Make prompts

Then, concatenate the few-shot training samples to make the prompt inputs. Please read the bash file to gain more information and edit the file to change the config.

```
bash make_prompts_shot.sh
```

After this process, you will get the `train_shot{shot_num}_seed{seed_num}_prompt.txt` files in the `processed_data/{dataset_name}_shot/{style}/{method}/{tag}` folder. One line in each file will look like the following sample:

```
def named_entity_recognition(input_text):
	""" extract named entities from the input_text . """
	input_text = "Bilateral relations and the Middle East peace process would be on the table during the visit , Akbel said ."
	entity_list = []
	# extracted named entities
	entity_list.append({"text": "Middle East", "type": "location"})
	entity_list.append({"text": "Akbel", "type": "person"})
# END

def named_entity_recognition(input_text):
	""" extract named entities from the input_text . """
	input_text = "Three plugged water injection wells on the Heidrun oilfield off mid-Norway will be reopened over the next month , operator Den Norske Stats Oljeselskap AS ( Statoil ) said on Thursday ."
	entity_list = []
	# extracted named entities
	entity_list.append({"text": "Heidrun", "type": "location"})
	entity_list.append({"text": "mid-Norway", "type": "miscellaneous"})
	entity_list.append({"text": "Den Norske Stats Oljeselskap AS", "type": "organization"})
	entity_list.append({"text": "Statoil", "type": "organization"})
# END

...
```

- Run Inference
Then, query OpenAI's models to get the generated outputs. Please read the bash file to gain more information and edit the file to change the config.

```
bash query_api_shot.sh
```

After this process, you will get the `${ENGINE}_returned_${splits}_shot${shot_idx}_seed${seed_idx}.jsonl` files in the `outputs/{dataset_name}_shot/{style}/{method}/{tag}` folder. Each line in each file will look like the following sample:

```json
{
    "text":"...",
    "tokens":[...],
    "entity":[],"relation":[],"event":[],"spot":[],"asoc":[],"spot_asoc":[],
    "input_idx":0,
    "input_prompt":"def relation_extraction(input_text):\n\t\"\"\" extract the relations of named entities from the input_text . \"\"\"\n\tinput_text = \"...\"\n\tentity_relation_list = []\n\t# extracted relations",
    "reference_output":"def relation_extraction(input_text):\n\t\"\"\" extract the relations of named entities from the input_text . \"\"\"\n\tinput_text = \"...\"\n\tentity_relation_list = []\n\t# extracted relations\n",
    "codex_response":{
        "id":"...",
        "object":"text_completion",
        "created":...,
        "model":"...",
        "choices":[...],
        "usage":{"prompt_tokens":...,"completion_tokens":...,"total_tokens":...}
    },
    "generated_code":"def relation_extraction(input_text):\n\t\"\"\" extract the relations of named entities from the input_text . \"\"\"\n\tinput_text = \"...\"\n\tentity_relation_list = []\n\t# extracted relations ...",
    "elapsed_time":...,
    "id":...}
```

### Evaluation

Finally, extract the predicted structures and evaluate the results. Please read the bash file to gain more information and edit the file to change the config.

```
bash evaluate_shot.sh
```

After this process, you will get the `${ENGINE}_returned_${splits}_shot${shot_num}_seed${seed_idx}_extraction.json` files in the `outputs/{dataset_name}_shot/{style}/{method}/{tag}` folder. Each line in each file will look like the following sample:

```json
{
    "entity":{
        "offset":[["location",[...]],["location",[...]]],
        "string":[["location","..."],["location","..."]]
    },
    "relation":{
        "offset":[],
        "string":[]
    },
    "event":{
        "offset":[],"string":[]
    },
    "statistic":{
        "ill-formed":...,
        "Invalid-Label":...,
        "Invalid-Text-Span":...,
        "Invalid-Label-asoc":...,
        "Invalid-Text-Span-asoc":...
    }
}
```

And you will also get the statistic file `${ENGINE}_returned_${splits}_shot${shot_num}_seed${seed_idx}_extraction_eval_stat.txt` like this:

```
test_string-ent-tp=...
test_string-ent-gold=...
test_string-ent-pred=...
test_string-ent-P=...
test_string-ent-R=...
test_string-ent-F1=...
test_offset-ent-tp=...
test_offset-ent-gold=...
test_offset-ent-pred=...
test_offset-ent-P=...
test_offset-ent-R=...
test_offset-ent-F1=...
test_offset-rel-strict-tp=
```

## Citation
If the paper or this repository helps you, please cite our paper:

```
@inproceedings{DBLP:conf/acl/LiSTYWHQ23,
  author       = {Peng Li and
                  Tianxiang Sun and
                  Qiong Tang and
                  Hang Yan and
                  Yuanbin Wu and
                  Xuanjing Huang and
                  Xipeng Qiu},
  editor       = {Anna Rogers and
                  Jordan L. Boyd{-}Graber and
                  Naoaki Okazaki},
  title        = {CodeIE: Large Code Generation Models are Better Few-Shot Information
                  Extractors},
  booktitle    = {Proceedings of the 61st Annual Meeting of the Association for Computational
                  Linguistics (Volume 1: Long Papers), {ACL} 2023, Toronto, Canada,
                  July 9-14, 2023},
  pages        = {15339--15353},
  publisher    = {Association for Computational Linguistics},
  year         = {2023},
  url          = {https://doi.org/10.18653/v1/2023.acl-long.855},
  doi          = {10.18653/V1/2023.ACL-LONG.855},
  timestamp    = {Fri, 16 Feb 2024 08:27:36 +0100},
  biburl       = {https://dblp.org/rec/conf/acl/LiSTYWHQ23.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```