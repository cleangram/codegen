import abc
from dataclasses import dataclass as dc
from textwrap import wrap
from typing import Literal

from .comps import TELEGRAM_PATH, TELEGRAM_OBJECT
from .enums import PackageType, CategoryType
from .models import Api, Component


@dc
class Template(abc.ABC):
    api: Api

    def __str__(self):
        return ""


@dc
class VersionTemplate(Template):
    def __str__(self):
        return f"""
import importlib.metadata

__version__ = importlib.metadata.version("cleangram")
__bot_api__ = "{self.api.version}"
"""


@dc
class PackageTemplate(Template):
    package: PackageType
    import_section: str = ""
    declaration_section: str = ""
    arguments_section: str = ""
    methods_section: str = ""

    def __call__(
            self,
            var: Literal[
                "import",
                "declaration",
                "arguments",
                "methods"
            ],
            val: str,
            tc: int,
            nl: int = 0
    ):
        section: str = getattr(self, f"{var}_section")
        new_val = section + (tc * '\t') + val + (nl * '\n')
        setattr(self, f"{var}_section", new_val)

    def i(self, val: str = "", tc=0, nl=1):
        self("import", val, tc, nl)

    def d(self, val: str = "", tc=0, nl=1):
        self("declaration", val, tc, nl)

    def a(self, val: str = "", tc=1, nl=1):
        self("arguments", val, tc, nl)

    def m(self, val: str = "", tc=1, nl=1):
        self("methods", val, tc, nl)

    def __str__(self):
        return "\n".join([
            self.import_section,
            self.declaration_section,
            self.arguments_section,
            self.methods_section
        ]).replace("\t", "    ")

    def __post_init__(self):
        self.is_core = self.package == PackageType.CORE
        self.is_aio = self.package == PackageType.AIO
        self.is_sync = self.package == PackageType.SYNC
        self.await_ = "await " if self.is_aio else ""
        self.async_ = "async " if self.is_aio else ""


@dc
class ComponentTemplate(PackageTemplate, abc.ABC):
    com: Component = None

    def header(self): ...

    @abc.abstractmethod
    def declaration(self): ...

    def description(self):
        self.a('"' * 3)
        for p in self.com.desc:
            for pp in wrap(p.text):
                self.a(pp)
            if self.is_core and self.com.subclasses:
                self.a()
                for sub in self.com.subclasses:
                    self.a(f":class:`cleangram.{sub.camel}`", tc=2)
        self.a()
        self.a("Reference: https://core.telegram.org/bots/api{self.com.anchor}")
        self.a('"' * 3)

    def arguments(self):
        if self.is_core:
            if self.com.has_field:
                self.i("from pydantic import Field")
            for arg in self.com.args:
                self.a(f"{arg.field}: {arg.annotation}{arg.class_value}")
                if arg.desc:
                    desc = '\n\t'.join(wrap(arg.desc.text))
                    self.a(f'"""{desc}"""\n')

    @abc.abstractmethod
    def methods(self): ...

    def write_typing(self, *types: str):
        for tp in types:
            self.i(f"from typing import {tp}")

    def __post_init__(self):
        super(ComponentTemplate, self).__post_init__()
        self.header()
        self.declaration()
        self.description()
        self.arguments()
        self.methods()


@dc
class ObjectTemplate(ComponentTemplate):
    def header(self):
        super(ObjectTemplate, self).header()
        if self.is_core:
            self.i("from __future__ import annotations")

    def declaration(self):
        extends = []
        if self.is_core:
            self.i(f"from .{self.com.parent.module} import {self.com.parent.camel}")
            extends.append(self.com.parent.camel)
            if self.com.is_adjusted:
                self.i("import abc")
                extends.append("abc.ABC")
        else:
            self.i(f"from ...core import {self.com.camel} as _{self.com.camel}")
            extends.append(f"_{self.com.camel}")
        self.d(f"class {self.com.camel}({','.join(extends)}):", nl=0)

    def arguments(self):
        super(ObjectTemplate, self).arguments()
        if self.is_core:
            self.write_typing(*self.com.args_typing)
            if self.com.args_objects:
                self.i("from typing import TYPE_CHECKING")
                self.i("if TYPE_CHECKING:")
                for tp in self.com.args_objects:
                    self.i(f"from .{tp.module} import {tp.camel}", 1)

    def methods(self):
        pass


@dc
class PathTemplate(ComponentTemplate):
    def declaration(self):
        extends = []
        if self.is_core:
            self.i("import abc")
            self.i(f"from .{self.com.parent.module} import {self.com.parent.camel}")
            extends.append(self.com.parent.camel)
            extends.append("abc.ABC")
        else:
            self.i(f"from ...core.paths.{self.com.module} import {self.com.camel} as _{self.com.camel}")
            extends.append(f"_{self.com.camel}")
            self.i("from ...core.objects.response import Response")
            self.write_typing(*self.com.result_typing)
            for tp in self.com.result_objects:
                self.i(f"from ..objects import {tp.camel}")
            extends.append(f"response=Response[{self.com.result.annotation}]")
        self.d(f"class {self.com.camel}({','.join(extends)}):", nl=0)

    def arguments(self):
        super(PathTemplate, self).arguments()
        if self.is_core:
            self.write_typing(*self.com.args_typing)
            for obj in self.com.args_objects:
                self.i(f"from ..objects import {obj.camel}")

    def methods(self):
        pass


@dc
class InitComponentsTemplate(PackageTemplate):
    ct: CategoryType = None

    def __post_init__(self):
        super(InitComponentsTemplate, self).__post_init__()
        coms = []
        if self.ct == CategoryType.OBJECT:
            coms = self.api.objects.copy()
            coms.extend([
                TELEGRAM_OBJECT
            ])
        elif self.ct == CategoryType.PATH:
            coms = self.api.paths.copy()
            coms.append(TELEGRAM_PATH)

        coms.sort(key=str)

        if self.is_core or self.ct == CategoryType.PATH:
            for com in coms:
                self.i(f"from .{com.module} import {com.camel}")
        else:
            for com in coms:
                self.i(f"from ...core {com.camel}")

        self.d("__all__ = [")
        for com in coms:
            self.d(f'{com.camel!r},', 1)
        self.d("]")
