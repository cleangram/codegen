from __future__ import annotations

from dataclasses import dataclass as dc
from dataclasses import field
from functools import lru_cache
from typing import List, Optional, Set, Union

from bs4 import Tag

from .enums import CategoryType
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
    def field_value(self):
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
    def method_value(self) -> str:
        return "=None" if self.optional else ""

    @property
    @lru_cache()
    def annotation(self) -> str:
        none = {"None"} if self.union and self.optional else set()

        return wrap(
            "Optional",
            self.optional and not self.union,
            wrap(
                "List",
                self.array == 2,
                wrap(
                    "List",
                    self.array,
                    wrap(
                        "Union",
                        self.union,
                        ", ".join(map(str, {*self.std_types, *self.com_types, *none})),
                    ),
                ),
            ),
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
    desc: List[Tag] = field(default_factory=list)
    has_field: bool = False
    subclasses: List[Component] = field(default_factory=list)

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
    def module(self) -> str:
        return self._module if self._module else self.snake

    @property
    def args_objects(self) -> Set[Component]:
        return {t for a in self.args for t in a.com_types if t != self}

    @property
    def result_objects(self) -> Set[Component]:
        return {*self.result.com_types}

    @property
    def used_objects(self) -> Set[Component]:
        return {*self.args_objects, *self.result_objects}

    @property
    def args_typing(self) -> Set[str]:
        return self.get_typing(*self.args)

    @property
    def result_typing(self) -> Set[str]:
        return self.get_typing(self.result)

    @property
    def used_typing(self) -> Set[str]:
        return {*self.args_typing, *self.result_typing}

    @property
    def is_adjusted(self):
        return self.name != "InputFile"

    @staticmethod
    def get_typing(*args: Argument):
        return {
            tp
            for a in args
            for tp, val in {
                "Optional": a.optional and not a.union,
                "Union": a.union,
                "List": a.array,
            }.items()
            if val
        }

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.camel

    def __eq__(self, other):
        if isinstance(other, Component):
            return self.name == other.name


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

    @lru_cache()
    def get_by_name(self, name: str) -> Component:
        for h in self.headers:
            for c in h.components:
                if c.name == name:
                    return c

    @property
    @lru_cache()
    def paths(self):
        return [c for h in self.headers for c in h.components if c.is_path]

    @property
    @lru_cache()
    def objects(self):
        return [c for h in self.headers for c in h.components if c.is_object]

    def __hash__(self):
        return hash(self.version)
