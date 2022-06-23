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
        for c in h.components:
            if c.name == "InputMedia":
                for s in c.subclasses:
                    typer.echo(s.name)
                    for a in s.args:
                        typer.echo(f"\t{a.name}: {a.annotation}{a.class_value}")

        # typer.echo(f"{h.name}")
        #     if c.subclasses:
        #         typer.echo(f"{c}({c.parent})")
        #         for s in c.subclasses:
        #             typer.echo(f"\t{s}({s.parent})")
            # if c.is_path:
            #     typer.echo(f"\t{c.name} -> {c.result.annotation}")
            #     for p in c.desc:
            #         for w in wrap(p):
            #             typer.echo(f"\t\t{w}")
    #                 typer.echo()
            # for a in c.args:
            #     print(f"\t\t{a.field}: {a.annotation}{a.class_value}")
                # typer.echo(f"\t\t{a.field}{a.class_value}")
        #     break
        # break
