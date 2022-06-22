import re
from typing import List, Optional, Dict

import h11
import httpx
from bs4 import BeautifulSoup, Tag
from . import comps, const
from .models import Api, Header, Component, Argument


def get_content() -> Tag:
    html = httpx.get("https://core.telegram.org/bots/api").text
    soup = BeautifulSoup(html, features="html.parser")
    return soup.find("div", id="dev_page_content")


def parse_version(content: Tag) -> str:
    return content\
        .find(
            name="strong",
            text=re.compile(r"^Bot API")
        )\
        .text\
        .removeprefix("Bot API")


def parse_args(component: Component, anchors: Dict[str, Component]):
    """
    Parse component arguments

    :param component:
    :return:
    """
    table = None
    for sub in component.tag.next_siblings:  # type: Tag
        if sub.name:
            if sub.name == "table":
                table = sub
                break
            elif sub.name == "h4":
                return

    # is table has 3 columns
    three: bool = len(table.thead.find_all("th")) == 3

    # parse rows
    for tr in table.tbody.find_all("tr"):
        td = tr.find_all("td")
        desc: Tag = td[2] if three else td[3]
        optional = "Optional" in td[2].text
        arg = Argument(
            name=td[0].text,
            desc=desc,
            array=td[1].text.count("rray of"),
            optional=optional,
            std_types=list({v for k, v in const.STD_TYPES.items() if k in td[1].text}),
            com_types=[anchors[tag["href"]] for tag in td[1].findAll("a")],
            default=(
                em.text if (
                        (em := desc.find("em")) and
                        not optional and
                        "must be" in desc.text
                ) else None
            ),
            component=component
        )
        if "Field" in arg.class_value:
            component.has_field = True
        component.args.append(arg)
    component.args.sort(key=lambda c: c.optional)
    component.args.sort(key=lambda c: bool(c.default))


def parse_component(tag: Tag) -> Component:
    component = Component(
        name=tag.text,
        anchor=tag.a["href"],
        tag=tag,
        parent=comps.TELEGRAM_OBJECT if tag.text.isupper() else comps.TELEGRAM_PATH
    )
    for sub in tag.next_siblings:  # type: Tag
        if sub.name and sub.text:
            if sub.name == "h4":
                break
            if sub.name == "p":
                component.desc.append(sub.text)
                component.raw_desc.append(sub)
    return component


def parse_components(headers: List[Header]):
    # Parse components by header
    for head in headers:
        for sub in head.tag.next_siblings:  # type: Tag
            if sub.name == "h3":
                break
            if sub.name == "h4" and " " not in sub.text:
                head.components.append(parse_component(sub))


def parse_headers(content: Tag) -> List[Header]:
    # Parsing headers
    is_start: bool = False
    headers: List[Header] = []
    for h3 in content.find_all("h3"):
        if h3.text == "Getting updates":
            is_start = True
        if is_start:
            headers.append(Header(
                name=h3.text,
                anchor=h3.a["href"],
                tag=h3
            ))
    parse_components(headers)
    anchors: Dict[str, Component] = {c.anchor: c for h in headers for c in h.components}
    for h in headers:
        for c in h.components:
            parse_args(c, anchors)
    return headers


def get_api() -> Api:
    content = get_content()
    return Api(
        version=parse_version(content),
        headers=parse_headers(content)
    )
