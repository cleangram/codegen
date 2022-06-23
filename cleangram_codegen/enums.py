from enum import Enum


class CategoryType(Enum):
    PATH: str = "path"
    OBJECT: str = "object"


class PackageType(Enum):
    CORE: str = "core"
    AIO: str = "aio"
    SYNC: str = "sync"
