#!/bin/bash
# run this file with "bash scripts/make_task_files.sh"

export PYTHONPATH=./

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
dataset_names=("conll03" "mrc_ace04" "mrc_ace05")
config_type=first_offset_en

for dataset_name in "${dataset_names[@]}"; do
  out_dir=processed_data/${dataset_name}_shot/${style}/${method}/${tag}
  if [ ! -d "$out_dir"  ]; then
    mkdir -p $out_dir
  fi
  for split in "train" "val" "test"; do
    python src/prompt/make_task_file.py \
    --inpath data/${dataset_name}_shot/seed1/1shot/${split}.json \
    --outpath ${out_dir}/${split}.jsonl \
    --job_type ${task}-${style}-${method} \
    --schema_path data/${dataset_name} \
    --map_config_path config/offset_map/${config_type}.yaml  &
  done

  split="train"
  for shot_idx in $(seq 1 $max_shot); do
    for seed_idx in $(seq 1 $seed_num); do
      python src/prompt/make_task_file.py \
      --inpath data/${dataset_name}_shot/seed${seed_idx}/${shot_idx}shot/${split}.json \
      --outpath ${out_dir}/${split}_shot${shot_idx}_seed${seed_idx}.jsonl \
      --job_type ${task}-${style}-${method} \
      --schema_path data/${dataset_name}\
      --map_config_path config/offset_map/${config_type}.yaml  &
    done
  done
  wait
done

## re
task=re
dataset_names=("conll04" "ace05-rel" "NYT" "scierc")
config_type=closest_offset_en

for dataset_name in "${dataset_names[@]}"; do
  out_dir=processed_data/${dataset_name}_shot/${style}/${method}/${tag}
  if [ ! -d "$out_dir"  ]; then
    mkdir -p $out_dir
  fi
  for split in "train" "val" "test"; do
    python src/prompt/make_task_file.py \
    --inpath data/${dataset_name}_shot/seed1/1shot/${split}.json \
    --outpath ${out_dir}/${split}.jsonl \
    --job_type ${task}-${style}-${method} \
    --schema_path data/${dataset_name} \
    --map_config_path config/offset_map/${config_type}.yaml  &
  done

  split="train"
  for shot_idx in $(seq 1 $max_shot); do
    for seed_idx in $(seq 1 $seed_num); do
      python src/prompt/make_task_file.py \
      --inpath data/${dataset_name}_shot/seed${seed_idx}/${shot_idx}shot/${split}.json \
      --outpath ${out_dir}/${split}_shot${shot_idx}_seed${seed_idx}.jsonl \
      --job_type ${task}-${style}-${method} \
      --schema_path data/${dataset_name} \
      --map_config_path config/offset_map/${config_type}.yaml  &
    done
  done
  wait
done