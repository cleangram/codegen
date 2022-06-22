import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup, Tag
from cleangram_codegen import comps

from .models import Api, Header, Component


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

    # Parse components by header
    for head in headers:
        for sub in head.tag.next_siblings:  # type: Tag
            if sub.name == "h3":
                break
            if sub.name == "h4" and " " not in sub.text:
                head.components.append(parse_component(sub))
                break
        break
    return headers


def get_api() -> Api:
    content = get_content()
    return Api(
        version=parse_version(content),
        headers=parse_headers(content)
    )
