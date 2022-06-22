import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup, Tag

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
    return Component(
        name=tag.text,
        anchor=tag.a["href"],
        tag=tag
    )


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

    # component: Optional[Component] = None
    # header: Optional[Header] = None
    # paragraph: str = ""

    #
    # for head in raw_headers:
    #     print(head.text)
    #     for sub in head.next_siblings:  # type: Tag
    #         if sub.name == "h3":
    #             break
    #         if sub.name == "h4":
    #             print("\t", sub.text)
    #
    #             break
    #     break




    # for tag in content.children:  # type: Tag
    #     if tag.name is None:
    #         continue
    #     if tag.text == "Getting updates":
    #         is_start = True
    #     if is_start:
    #         if tag.name == "h3":
    #             component = None
    #             headers.append((header := Header(name=tag.text)))
    #         elif header:
    #             if tag.name == "h4":
    #                 header.components.append((current := Component(tag.text)))
    # if current := parse_component(tag):
    #     header.components.append(current)
    #     elif current:
    #         if tag.name == "p":
    #             current.paragraphs.append(tag.text)
    #             if isinstance(current, Path):
    #                 if not current.result.types:
    #                     current.result = parse_result(tag)
    #         elif tag.name == "ul":
    #             for sub in tag.find_all("li"):
    #                 current.subclasses.append(sub.a["href"])
    #         elif tag.name == "table":
    #             current.args = parse_args(tag)
    #             current = None

    return headers


def get_api() -> Api:
    content = get_content()
    return Api(
        version=parse_version(content),
        headers=parse_headers(content)
    )
