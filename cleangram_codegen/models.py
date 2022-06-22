from __future__ import annotations

from dataclasses import dataclass as dc, field
from functools import lru_cache
from typing import List, Optional

from bs4 import Tag
from cleangram_codegen.util import snake

from .const import CategoryType


@dc
class Argument:
    name: str = ""

    def __bool__(self):
        return bool(self.name)


@dc
class Component:
    name: str
    anchor: Optional[str] = field(default=None, repr=False)
    tag: Optional[Tag] = field(default=None, repr=False)
    args: List[Argument] = field(default_factory=list, repr=False)
    result: Argument = field(repr=False, default_factory=Argument)
    _module: Optional[str] = field(default=None, repr=False)
    parent: Optional[Component] = None
    desc: List[str] = field(default_factory=list)
    raw_desc: List[Tag] = field(default_factory=list)

    @property
    def is_path(self):
        return self.category == CategoryType.PATH

    @property
    def is_object(self):
        return self.category == CategoryType.OBJECT

    @property
    def snake(self):
        return snake(self.name)

    @property
    @lru_cache()
    def category(self):
        return CategoryType.OBJECT if self.name[0].isupper() else CategoryType.PATH

    @property
    @lru_cache()
    def module(self):
        return self._module if self._module else self.snake

    def __hash__(self):
        return hash(self.name)


@dc
class Header:
    name: str
    anchor: str
    tag: Tag
    components: List[Component] = field(default_factory=list)


@dc
class Api:
    version: str
    headers: List[Header]
