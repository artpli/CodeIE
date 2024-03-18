

class StructureConverter(object):


    def structure_to_input(self, input_dict: dict, prompt_part_only: bool = False) -> str:

        raise NotImplementedError()

    def output_to_structure(self, input_dict: dict, output_str: str):

        raise NotImplementedError()


    @staticmethod
    def to_function_head(s,input=''):
        return f'def {s}({input}):'

    @staticmethod
    def to_function_name(s):
        s = s.replace(".", "").replace(",", "")
        # remove DT
        tok = s.lower().split()
        tok = [x for x in tok if x not in ['the', 'a', 'an']]
        return '_'.join(tok)

    @staticmethod
    def list_to_str(l):
        # remove \n
        l = [x.replace("\n", " ") if x != '\n' else '' for x in l]
        l = '\n'.join(l)
        return l