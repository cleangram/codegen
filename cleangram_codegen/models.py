from __future__ import annotations

from dataclasses import dataclass as dc, field
from functools import lru_cache
from typing import List, Optional, Union

from bs4 import Tag

from .const import CategoryType
from .util import snake, wrap


@dc(repr=False)
class Argument:
    name: str = ""
    desc: Optional[Tag] = None
    array: int = 0
    optional: bool = False
    default: Optional[str] = None
    component: Optional[Component] = None
    std_types: List[str] = field(default_factory=list)
    com_types: List[Union[str, Component]] = field(default_factory=list)

    @property
    @lru_cache()
    def union(self):
        return (len(self.std_types) + len(self.com_types)) > 1

    @property
    @lru_cache()
    def field(self) -> str:
        if self.name in {"from"}:
            return f"{self.name}_"
        return self.name

    @property
    @lru_cache()
    def class_value(self):
        if self.name in {"from"}:
            return f" = Field(alias={self.name!r})"
        elif self.default:
            return f" = {self.default!r}"
        elif self.array and self.component and self.component.is_object:
            return f" = Field(default_factory=list)"
        elif self.optional:
            return f" = None"
        else:
            return ""

    @property
    @lru_cache()
    def annotation(self) -> str:
        none = ["None"] if self.union and self.optional else []

        return wrap(
            "Optional", self.optional and not self.union, wrap(
                "List", self.array == 2, wrap(
                    "List", self.array, wrap(
                        "Union",
                        self.union,
                        ", ".join(map(str, [
                            *self.std_types,
                            *self.com_types,
                            *none
                        ]))
                    )
                )
            )
        )

    def __bool__(self):
        return bool(self.std_types) or bool(self.com_types)

    def __hash__(self):
        return hash(self.name)


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
    has_field: bool = False

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
    def camel(self):
        return self.name[0].upper() + self.name[1:]

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

    def __str__(self):
        return self.camel


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
