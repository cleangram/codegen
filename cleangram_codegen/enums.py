from enum import Enum


class CategoryType(Enum):
    PATH: str = "paths"
    OBJECT: str = "objects"


class PackageType(Enum):
    CORE: str = "core"
    AIO: str = "aio"
    SYNC: str = "sync"
