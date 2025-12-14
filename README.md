# CodeIE

This is the official repository for "[CodeIE: Large Code Generation Models are Better Few-Shot Information Extractors](https://arxiv.org/abs/2305.05711)" (ACL 2023).    

If you have any questions or suggestions, please feel free to open issues or email Peng Li (lip21 [at] m.fudan.edu.cn). 

## Introduction

Our codebase is mainly modified from the [UIE](https://github.com/universal-ie/UIE) and [CoCoGen](https://github.com/reasoning-machines/CoCoGen) repositories.
We obtained and processed the original NER and RE datasets according to UIE's workflow.
Then we implemented the inference logic of CodeIE referring to CoCoGen's workflow.
Finally we evaluated the model outputs based on UIE's evaluation process.

We sincerely thank these two works and previous works.

## Workflow
Please refer to the [workflow.md](./workflow.md) file.

## Notice
1. A piece of not-so-good news is that the `Codex` models are now [deprecated by OpenAI](https://platform.openai.com/docs/guides/code). Some possible solutions include applying for OpenAI's [Researcher Access Program](https://openai.com/form/researcher-access-program) or accessing Codex on [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/work-with-code).
2. Since we are using the closed-source APIs of OpenAI, we are unaware of the technical details behind them, such as the specific pre-training corpora used. Therefore, there might be potential issues of [data contamination](https://hitz-zentroa.github.io/lm-contamination/blog/) in the evaluation of our paper. (Acknowledgement: [Oscar Sainz](https://osainz59.github.io/))


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
