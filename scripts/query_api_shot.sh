#!/bin/bash
# link: https://learn.microsoft.com/en-us/azure/cognitive-services/openai/concepts/models
# GPT3: text-davinci-002
# CodeX: code-davinci-002

export PYTHONPATH=./
export OPENAI_API_KEY="" #<YOUR OPENAI KEY>

declare -A OPENAI_KEYS
OPENAI_KEYS["conll03"]=(${OPENAI_API_KEY})
OPENAI_KEYS["mrc_ace04"]=(${OPENAI_API_KEY})
OPENAI_KEYS["mrc_ace05"]=(${OPENAI_API_KEY})

OPENAI_KEYS["conll04"]=(${OPENAI_API_KEY})
OPENAI_KEYS["ace05-rel"]=(${OPENAI_API_KEY})
OPENAI_KEYS["NYT"]=(${OPENAI_API_KEY})
OPENAI_KEYS["scierc"]=(${OPENAI_API_KEY})

declare -A SHOT_NUMS
SHOT_NUMS["conll03"]=5
SHOT_NUMS["mrc_ace04"]=2
SHOT_NUMS["mrc_ace05"]=2
SHOT_NUMS["conll04"]=5
SHOT_NUMS["ace05-rel"]=2
SHOT_NUMS["NYT"]=1
SHOT_NUMS["scierc"]=2

GPU=0
NUM_TASKS=1
splits="test"
prompt_splits="train"

####################
#style=nl
#method=sel
#tag=sel

style=pl
method=func
tag=func
####################


####################
#ENGINE=text-davinci-002
#MAX_REQUESTS_PER_MIN=50
#
ENGINE=code-davinci-002
MAX_REQUESTS_PER_MIN=18
####################

####################
#
task=ner
dataset_names=("conll03" "mrc_ace04" "mrc_ace05")
config_type=first_offset_en

# task=re
# dataset_names=("conll04" "ace05-rel" "NYT" "scierc")
# config_type=closest_offset_en
####################

seed_num=(1 2 3)
start_cut_num=0
declare -A OUTPUT_FILE_LIST
for seed_idx in ${seed_num[@]}; do
  for dataset_name in "${dataset_names[@]}"; do
    shot_idx=${SHOT_NUMS[$dataset_name]}

    base_in_dir=processed_data/${dataset_name}_shot/${style}/${method}/${tag}
    base_out_dir=outputs/${dataset_name}_shot/${style}/${method}/${tag}
    if [ ! -d "$base_out_dir"  ]; then
      mkdir -p $base_out_dir
    fi
    in_dir=${base_in_dir}/${splits}.jsonl
    prompt_dir=${base_in_dir}/${prompt_splits}_shot${shot_idx}_seed${seed_idx}_prompt.txt

    codex_keys=${OPENAI_KEYS[$dataset_name]}
    codex_keys=($codex_keys)
    codex_keys_num=${#codex_keys[*]}

    out_files=()
    for key_id in $(seq 0 $[$codex_keys_num-1]); do
      export OPENAI_API_KEY=${codex_keys[$key_id]}
      START_IDX=$[NUM_TASKS*$key_id]
      END_IDX=$((START_IDX+NUM_TASKS))

      output_file_path=$base_out_dir/${ENGINE}_returned_${splits}_shot${shot_idx}_seed${seed_idx}_${START_IDX}_${END_IDX}.jsonl
      out_files=(${out_files[@]} $output_file_path)
      CUDA_VISIBLE_DEVICES=$GPU python -u src/api/query_openai_over_tasks.py \
      --task_file_path ${in_dir} \
      --num_tasks ${NUM_TASKS} \
      --start_idx ${START_IDX} \
      --output_file_path ${output_file_path} \
      --prompt_path  ${prompt_dir} \
      --job_type ${task}-${style}-${method} \
      --schema_path data/${dataset_name} \
      --map_config_path config/offset_map/${config_type}.yaml \
      --engine ${ENGINE} \
      --max_requests_per_min ${MAX_REQUESTS_PER_MIN} \
      --start_cut_num ${start_cut_num} &
    done
    OUTPUT_FILE_LIST[${dataset_name}]=${out_files[@]}
  done
  wait
  for dataset_name in "${dataset_names[@]}"; do
    base_out_dir=outputs/${dataset_name}_shot/${style}/${method}/${tag}
    out_files=${OUTPUT_FILE_LIST[${dataset_name}]}
    out_files=($out_files)
    cat "${out_files[@]}" > $base_out_dir/${ENGINE}_returned_${splits}_shot${shot_idx}_seed${seed_idx}.jsonl
    for f in "${out_files[@]}"; do
      rm "$f"
    done
  done
  echo "Good job!"
done