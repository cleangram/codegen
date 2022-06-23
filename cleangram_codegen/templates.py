import abc
from dataclasses import dataclass as dc

from .models import Api


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
