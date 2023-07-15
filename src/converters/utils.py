import re
import sys
from typing import Tuple


def match_sublist(the_list, to_match):
    """
    :param the_list: [1, 2, 3, 4, 5, 6, 1, 2, 4, 5]
    :param to_match: [1, 2]
    :return:
        [(0, 1), (6, 7)]
    """
    len_to_match = len(to_match)
    matched_list = list()
    for index in range(len(the_list) - len_to_match + 1):
        if to_match == the_list[index:index + len_to_match]:
            matched_list += [(index, index + len_to_match - 1)]
    return matched_list


def check_overlap(x, y):
    if x[0] > y[1] or y[0] > x[1]:
        return False
    else:
        return True


def get_index_tuple(matched: Tuple[int, int]):
    return tuple(range(matched[0], matched[1] + 1))


def span_to_token(text, span_to_token_strategy='space'):
    if span_to_token_strategy == 'space':
        return text.split(' ')
    elif span_to_token_strategy == 'list':
        return list(text)
    else:
        raise NotImplementedError(
            f"The span to token strategy {span_to_token_strategy} is not implemented.")


def to_camel_case(title: str) -> str:
    """Converts a proscript title to a camel case string.
    Example:
        title: travel to the theme park
        camel_case: TravelToThemePark
    """
    if "." == title[-1]:
        title = title[:-1]
    title_tokens = title.split(" ")
    title_camel_case = ""
    for token in title_tokens:
        title_camel_case += token.capitalize()
    return title_camel_case

def to_snake_case(name):
    # replace all space and punctuation with underscore
    if name[-1] == ".":
        name = name[:-1]

    name = re.sub(r'[\s\W]', '_', name)

    return name.lower().strip()

def from_snake_to_normal_str(snake_str: str) -> str:
    """Converts a snake case string to a normal string.
    Example:
        snake_str: travel_to_the_theme_park
        normal_str: travel to the theme park
    """
    return " ".join(snake_str.split("_"))

def compile_code_get_object(py_code_str: str):
    """Given python code as a string, compiles it 
    and returns an object of the class contained in the string.

    Args:
        code (str): _description_
    """
    # compile the code
    try:
        py_code = compile(py_code_str, "<string>", "exec")
    except SyntaxError:
        # try without the last k lines in py_code_str: usually the last line is incomplete
        for k in range(1, 3):
            try:
                lines = py_code_str.split("\n")
                lines = "\n".join(lines[:-k])
                py_code = compile(lines, "<string>", "exec")
            except SyntaxError as e:
                print(f"Error compiling python code:\n{py_code_str}")
                raise e

    # instantiate the class
    py_code_dict = {}
    exec(py_code, py_code_dict)
    # the newly instantiated class will be last in the scope
    py_code_class = py_code_dict[list(py_code_dict.keys())[-1]]()
    return py_code_class


