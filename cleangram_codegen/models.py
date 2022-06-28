from __future__ import annotations

from dataclasses import dataclass as dc
from dataclasses import field
from functools import lru_cache
from typing import List, Optional, Set, Union

from bs4 import Tag

from . import const
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

    @lru_cache()
    def __bool__(self):
        return bool(self.std_types) or bool(self.com_types)

    def __hash__(self):
        return hash(self.name)


    @lru_cache()
    def __str__(self):
        return self.field


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
    api: Optional[Api] = None

    @property
    @lru_cache()
    def is_path(self):
        return self.category == CategoryType.PATH

    @property
    @lru_cache()
    def is_object(self):
        return self.category == CategoryType.OBJECT

    @property
    @lru_cache()
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
    def module(self) -> str:
        return self._module if self._module else self.snake

    @property
    @lru_cache()
    def args_objects(self) -> Set[Component]:
        return {t for a in self.args for t in a.com_types if t != self}

    @property
    @lru_cache()
    def result_objects(self) -> Set[Component]:
        return {*self.result.com_types}

    @property
    @lru_cache()
    def used_objects(self) -> Set[Component]:
        return {*self.args_objects, *self.result_objects}

    @property
    @lru_cache()
    def args_typing(self) -> Set[str]:
        return self.get_typing(*self.args)

    @property
    @lru_cache()
    def result_typing(self) -> Set[str]:
        return self.get_typing(self.result)

    @property
    @lru_cache()
    def used_typing(self) -> Set[str]:
        return {*self.args_typing, *self.result_typing}

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

    @property
    @lru_cache()
    def is_adjusted(self):
        if self.api:
            if self.is_path:
                return self in self.api.adjusted_paths
            elif self.is_object:
                return self in self.api.adjusted_objects

    @property
    @lru_cache()
    def is_aliased(self):
        if self.is_object:
            return self in self.api.aliased_objects

    @property
    @lru_cache()
    def adjusted_objects(self):
        return [o for o in self.args_objects if o.is_adjusted]

    @property
    @lru_cache()
    def adjusted_typing(self):
        return self.get_typing(*{
            a for a in self.args if any([c.is_adjusted for c in a.com_types])
        })

    @property
    @lru_cache()
    def is_prepared(self):
        return self.is_path and (
                self.api.input_file in self.used_objects or
                self.name == "sendMediaGroup"
        )

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

    @property
    def paths(self):
        return [c for c in self.components if c.is_path]

    @property
    def objects(self):
        return [c for c in self.components if c.is_object]

    def __hash__(self):
        return hash(self.name)


@dc
class Api:
    version: str
    headers: List[Header]

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

    @property
    @lru_cache()
    def paths_objects(self):
        return sorted({o for p in self.paths for o in p.used_objects}, key=str)

    @property
    @lru_cache()
    def all_results_objects(self):
        return sorted({o for p in self.paths for o in p.result_objects}, key=str)

    @property
    @lru_cache()
    def aliased_objects(self):
        return [o for o in self.objects if o.name in const.ALIASED_OBJECTS]

    @property
    @lru_cache()
    def adjusted_objects(self):
        _adjusted_objects = set()

        def is_adjusted(c: Component):
            if c in self.aliased_objects or c in _adjusted_objects:
                _adjusted_objects.add(c)
                return True
            for o in c.used_objects:
                if is_adjusted(o):
                    _adjusted_objects.add(c)

        [is_adjusted(c) for c in self.all_results_objects]
        return _adjusted_objects

    @property
    @lru_cache()
    def adjusted_paths(self):
        return {p
                for p in self.paths
                if any([o in self.adjusted_objects for o in p.result_objects])
                }

    @property
    @lru_cache()
    def input_file(self):
        for o in self.objects:
            if o.name == "InputFile":
                return o

    @property
    @lru_cache()
    def update(self):
        for o in self.objects:
            if o.name == "Update":
                return o
