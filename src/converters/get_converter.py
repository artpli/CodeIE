# NER tasks
from src.converters.ner.structure2pl_func import PLFuncPromptCreator as NERPLFuncPromptCreator
from src.converters.ner.structure2nl_sel import NLSELPromptCreator as NERNLSELPromptCreator

# RE tasks
from src.converters.re.structure2pl_func import PLFuncPromptCreator as REPLFuncPromptCreator
from src.converters.re.structure2nl_sel import NLSELPromptCreator as RENLSELPromptCreator


class ConverterFactory:
    converter_to_class = {
        # ner
        "ner-pl-func": NERPLFuncPromptCreator,
        "ner-nl-sel": NERNLSELPromptCreator,

        # re
        "re-pl-func": REPLFuncPromptCreator,
        "re-nl-sel": RENLSELPromptCreator
    }
    supported_converters = list(converter_to_class.keys())

    @staticmethod
    def get_converter(job_type: str, **kwargs):
        if job_type not in ConverterFactory.supported_converters:
            raise ValueError(f"Unsupported job type: {job_type}")
        return ConverterFactory.converter_to_class[job_type](**kwargs)
