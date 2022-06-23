import pathlib
from textwrap import wrap

import typer

from .const import CODE_DIR
from .parser import get_api

cli = typer.Typer()


@cli.command(name="gen")
def gen(path: str = typer.Argument(CODE_DIR)):
    typer.echo(f"Generated to {pathlib.Path(path).absolute()}")


@cli.command(name="parse")
def parse():
    api = get_api()

    typer.echo(f"Version: {api.version}")

    for h in api.headers:
        typer.echo(f"{h.name}")
        for c in h.components:
            typer.echo(f"\t{c.name}({c.parent}){f' -> {c.result.annotation}' if c.is_path else ''}")
            for a in c.args:
                typer.echo(f"\t\t{a.name}: {a.annotation}{a.class_value}")
