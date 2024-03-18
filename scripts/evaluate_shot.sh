#!/bin/bash
export PYTHONPATH=./

declare -A SHOT_NUMS
SHOT_NUMS["conll03"]=5
SHOT_NUMS["mrc_ace04"]=2
SHOT_NUMS["mrc_ace05"]=2
SHOT_NUMS["conll04"]=5
SHOT_NUMS["ace05-rel"]=2
SHOT_NUMS["NYT"]=1
SHOT_NUMS["scierc"]=2


#task=ner
dataset_names=("conll03" "mrc_ace04" "mrc_ace05")
style=pl
method=func
config_type=first_offset_en
splits="test"
config_type_path=config/offset_map/${config_type}.yaml
ENGINE=code-davinci-002
tag=func-v5
stat_key=offset-ent-F1

# task=re
# dataset_names=("conll04" "ace05-rel" "NYT" "scierc")
# style=nl
# method=sel
# config_type=closest_offset_en
# splits="test"
# config_type_path=config/offset_map/${config_type}.yaml
# ENGINE=code-davinci-002
# tag=sel
# stat_key=test_offset-rel-strict-F1

stat_output_list=()
seed_num=3
for seed_idx in $(seq 1 $seed_num); do
  for dataset_name in "${dataset_names[@]}"; do

    shot_num=${SHOT_NUMS[$dataset_name]}
    output_dir=outputs/${dataset_name}_shot/${style}/${method}/${tag}

    api_returned_file=$output_dir/${ENGINE}_returned_${splits}_shot${shot_num}_seed${seed_idx}.jsonl

    python src/eval/extract_results.py \
    --raw_output_file ${api_returned_file} \
    --output_file  $output_dir/${ENGINE}_returned_${splits}_shot${shot_num}_seed${seed_idx}_extraction.json \
    --src_file processed_data/${dataset_name}_shot/${style}/${method}/${tag}/${splits}.jsonl \
    --job_type ${task}-${style}-${method} \
    --schema_path data/${dataset_name} \
    --map_config_path ${config_type_path}

    python3 ./src/eval/eval_extraction.py \
    -p ${output_dir} \
    -pf ${ENGINE}_returned_${splits}_shot${shot_num}_seed${seed_idx}_extraction.json \
    -g processed_data/${dataset_name}_shot/${style}/${method}/${tag} \
    -gf ${splits}.jsonl \
    -sf ${ENGINE}_returned_${splits}_shot${shot_num}_seed${seed_idx}_extraction_eval_stat.txt \
    -w -case -m ${eval_match_mode:-"normal"}

    out_file=$output_dir/${ENGINE}_returned_${splits}_shot${shot_num}_seed${seed_idx}_extraction_eval_stat.txt
    stat_line=$(cat "$out_file" | grep "$stat_key")
    stat_output_list=(${stat_output_list[@]} "${dataset_name}-seed${seed_idx}:$stat_line")
    echo "${dataset_name} seed${seed_idx} done."
  done
done

echo "Stat Summary: "
for item in "${stat_output_list[@]}"; do
  echo "$item"
done

echo "Good Job!"


