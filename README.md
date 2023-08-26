# CodeIE
[ACL23] CodeIE: Large Code Generation Models are Better Few-Shot Information Extractors     
[https://arxiv.org/abs/2305.05711](https://arxiv.org/abs/2305.05711)

Our code is mainly modified from the [UIE](https://github.com/universal-ie/UIE) and [CoCoGen](https://github.com/reasoning-machines/CoCoGen) code repositories. 
We have updated an initial version of the source file. More information about data processing and code will be provided in subsequent updates.


Notice: 
1. A piece of not-so-good news is that the Codex models are now [deprecated by OpenAI](https://platform.openai.com/docs/guides/code), which will have a significant impact on replicating this paper. Some possible solutions include applying for OpenAI's [Researcher Access Program](https://openai.com/form/researcher-access-program) or accessing Codex on [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/work-with-code).
2. Since we are using the closed-source APIs of OpenAI, we are unaware of the technical details behind them, such as the specific pre-training corpora used. Therefore, there might be potential issues of [data contamination](https://hitz-zentroa.github.io/lm-contamination/blog/) in the evaluation of our paper. If possible, we would evaluate our approach on more open-source models. (Acknowledgement: [Oscar Sainz](https://osainz59.github.io/))




**Citation**
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
  doi          = {10.18653/v1/2023.acl-long.855},
  timestamp    = {Thu, 10 Aug 2023 12:35:53 +0200},
  biburl       = {https://dblp.org/rec/conf/acl/LiSTYWHQ23.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```
