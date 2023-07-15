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
@misc{li2023codeie,
      title={CodeIE: Large Code Generation Models are Better Few-Shot Information Extractors}, 
      author={Peng Li and Tianxiang Sun and Qiong Tang and Hang Yan and Yuanbin Wu and Xuanjing Huang and Xipeng Qiu},
      year={2023},
      eprint={2305.05711},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```
