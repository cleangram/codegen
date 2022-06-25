import logging
import os
import pathlib
from typing import List, Type

import black
import isort

from .enums import PackageType, CategoryType
from .models import Component
from .parser import get_api
from .templates import Template, VersionTemplate, ObjectTemplate, PathTemplate, ComponentTemplate, \
    InitComponentsTemplate


def md(path: pathlib.Path):
    os.makedirs(path, exist_ok=True)


class Generator:
    def __init__(self, is_gen: bool = True):
        self.is_gen = is_gen
        self.api = get_api()
        self.mode = black.Mode(
            target_versions={black.TargetVersion.PY38},
            line_length=79,
            string_normalization=False,
            is_pyi=False,
        )
        self.root = pathlib.Path().absolute()
        self.code = self.root / "cleangram"
        self.log = logging.getLogger("Generator")

    def _gen(self, tmp: Template, path: pathlib.Path):
        # render
        txt = str(tmp)
        if path.suffix == ".py":
            try:
                txt = black.format_str(
                    isort.code(txt),
                    mode=self.mode
                )
            except Exception as e:
                self.log.exception(txt)
                raise e
        if self.is_gen:
            with open(path, "w", encoding="utf-8") as f:
                f.write(txt)
                self.log.info(path)
        else:
            self.log.info(f"{path}\n{txt}")

    def gen_version(self):
        self._gen(
            VersionTemplate(self.api),
            self.code / "_version.py"
        )

    def gen_init(self, pt: PackageType):
        for ct in CategoryType:
            path = self.code / pt.value / ct.value
            md(path)
            self._gen(
                InitComponentsTemplate(
                    api=self.api,
                    package=pt,
                    ct=ct),
                path / "__init__.py"
            )

    def gen_components(self, pt: PackageType):
        for category, Tmp, components in (
                (CategoryType.OBJECT, ObjectTemplate, self.api.objects),
                (CategoryType.PATH, PathTemplate, self.api.paths)
        ):
            for com in components:
                self._gen(
                    Tmp(
                        api=self.api,
                        package=pt,
                        com=com
                    ),
                    self.code / pt.value / category.value / f"{com.module}.py"
                )
                break  # render only first of object, path
            # break

    def run(self):
        # self.gen_version()
        for pt in PackageType:
            # self.gen_init(pt)
            # if pt == PackageType.AIO:
            self.gen_components(pt)
            break
