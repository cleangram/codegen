import logging
import pathlib
from textwrap import wrap

import typer

from .parser import get_api
from .generator import Generator

cli = typer.Typer()
logging.basicConfig(level=logging.INFO)


@cli.command(name="gen")
def gen():
    Generator(True).run()


@cli.command(name="render")
def render():
    Generator(False).run()


@cli.command(name="parse")
def parse():
    api = get_api()

    typer.echo(f"Version: {api.version}")

    for h in api.headers:
        typer.echo(f"{h.name}")
        for c in h.components:
            typer.echo(
                f"\t{c.name}({c.parent}){f' -> {c.result.annotation}' if c.is_path else ''}"
            )
            if c.is_path:
                typer.echo(f"\t\tRO: " + ",".join(map(str, c.result_objects)))
                typer.echo(f"\t\tRT: " + ",".join(map(str, c.result_typing)))
            typer.echo(f"\t\tAO: " + ",".join(map(str, c.args_objects)))
            typer.echo(f"\t\tAT: " + ",".join(map(str, c.args_typing)))
            typer.echo(f"\t\tUT: " + ",".join(map(str, c.used_typing)))
            typer.echo(f"\t\tUO: " + ",".join(map(str, c.used_objects)))
            typer.echo()
            for a in c.args:
                typer.echo(f"\t\t{a.name}: {a.annotation}{a.class_value}")
