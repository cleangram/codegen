from enum import Enum

CODE_DIR = "cleangram"
STD_TYPES = {
    "True": "bool",
    "String": "str",
    "Int": "int",
    "Float": "float",
    "Boolean": "bool",
    "Integer": "int",
}


class CategoryType(Enum):
    PATH: str = "path"
    OBJECT: str = "object"
