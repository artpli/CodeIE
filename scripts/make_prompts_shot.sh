#!/bin/bash
# bash scripts/make_prompts.sh

export PYTHONPATH=./

splits=("train")

style=pl
method=func
tag=func

#style=nl
#method=sel
#tag=sel

seed_num=5
max_shot=10

### ner
task=ner
task_type=entity
dataset_names=("conll03" "mrc_ace04" "mrc_ace05")
config_type=first_offset_en

for dataset_name in "${dataset_names[@]}"; do
  out_dir=processed_data/${dataset_name}_shot/${style}/${method}/${tag}
  for shot_idx in $(seq 1 $max_shot); do
    for seed_idx in $(seq 1 $seed_num); do
      for split in "${splits[@]}"; do
        python src/prompt/make_prompt.py -src ${out_dir}/${split}_shot${shot_idx}_seed${seed_idx}.jsonl \
        -tgt ${out_dir}/${split}_shot${shot_idx}_seed${seed_idx}_prompt.txt \
        -schema_file data/${dataset_name}/${task_type}.schema \
        -task ${task_type} \
        -n_examples -1 &
      done
    done
  done
  wait
done

### re
task=re
task_type=relation
dataset_names=("conll04" "ace05-rel" "NYT" "scierc")
config_type=closest_offset_en

for dataset_name in "${dataset_names[@]}"; do
  out_dir=processed_data/${dataset_name}_shot/${style}/${method}/${tag}
  for shot_idx in $(seq 1 $max_shot); do
    for seed_idx in $(seq 1 $seed_num); do
      for split in "${splits[@]}"; do
        python src/prompt/make_prompt.py -src ${out_dir}/${split}_shot${shot_idx}_seed${seed_idx}.jsonl \
        -tgt ${out_dir}/${split}_shot${shot_idx}_seed${seed_idx}_prompt.txt \
        -schema_file data/${dataset_name}/${task_type}.schema \
        -task ${task_type} \
        -n_examples -1 &
      done
    done
  done
  wait
done