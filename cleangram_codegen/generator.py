import logging
import os
import pathlib

import black
import isort

from .enums import PackageType
from .parser import get_api
from .templates import Template, VersionTemplate


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

    def run(self):
        self.gen_version()

        for pt in PackageType:
            md(self.code / pt.value)

    def gen_version(self):
        self._gen(
            VersionTemplate(self.api),
            self.code / "_version.py"
        )

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
            with(path, "w") as f:
                f.write(txt)
                self.log.info(path)
        else:
            self.log.info(f"{path}\n{txt}")
