import re
from typing import Dict, List, Optional

import h11
import httpx
from bs4 import BeautifulSoup, Tag

from . import comps, const
from .models import Api, Argument, Component, Header


def get_content() -> Tag:
    html = httpx.get("https://core.telegram.org/bots/api").text
    soup = BeautifulSoup(html, features="html.parser")
    return soup.find("div", id="dev_page_content")


def parse_version(content: Tag) -> str:
    return content.find(name="strong", text=re.compile(r"^Bot API")).text.removeprefix(
        "Bot API "
    )


def parse_args(component: Component, anchors: Dict[str, Component]):
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
                em.text
                if ((em := desc.find("em")) and not optional and "must be" in desc.text)
                else None
            ),
            component=component,
        )
        if "Field" in arg.field_value:
            component.has_field = True
        component.args.append(arg)
    component.args.sort(key=lambda c: c.optional)
    component.args.sort(key=lambda c: bool(c.default))


def parse_result(component: Component, anchors: Dict[str, Component]):
    result = component.result

    for p in component.desc:
        links = [i for i in p.find_all("a") if i["href"].startswith("#")]
        for phrase in p.text.replace(",", ".").split("."):
            if "eturn" in phrase:
                words = phrase.split()
                for link in links:
                    if link.text in words and p.text[0].isupper():
                        if anc := anchors.get(link["href"], None):
                            result.com_types.append(anc)
                for alias, tp in const.STD_TYPES.items():
                    if alias in words:
                        result.std_types.append(tp)
                if "rray of" in phrase:
                    result.array = phrase.count("rray of")


def parse_component(tag: Tag) -> Component:
    component = Component(
        name=tag.text,
        anchor=tag.a["href"],
        tag=tag,
        parent=comps.TELEGRAM_OBJECT if tag.text[0].isupper() else comps.TELEGRAM_PATH,
    )
    for sub in tag.next_siblings:  # type: Tag
        if sub.name and sub.text:
            if sub.name == "h4":
                break
            if sub.name == "p":
                component.desc.append(sub)
    return component


def parse_components(header: Tag) -> List[Component]:
    _comps = []
    for sub in header.next_siblings:  # type: Tag
        if sub.name == "h4" and " " not in sub.text:
            _comps.append(parse_component(sub))
        if sub.name == "h3":
            break
    return _comps


def parse_subclasses(component: Component, anchors: Dict[str, Component]):
    ul: Optional[Tag] = None
    for sub in component.tag.next_siblings:  # type: Tag
        if sub.name:
            if sub.name in {"h4", "h3"}:
                return
            elif sub.name == "ul":
                ul = sub
                break
    if ul:
        for li in ul.find_all("li"):
            sub_class = anchors[li.a["href"]]
            sub_class.parent = component
            component.subclasses.append(sub_class)


def process_input_media(api: Api):
    for h in api.headers:
        for c in h.components:
            if c.name.startswith("InputMedia"):
                for a in c.args:
                    if a.name == "media":
                        a.com_types.append(api.get_by_name("InputFile"))
            elif c.name == "sendMediaGroup":
                for a in c.args:
                    if a.name == "media":
                        a.com_types = [api.get_by_name("InputMedia")]


def parse_headers(content: Tag) -> List[Header]:
    # Parsing headers
    is_start: bool = False
    headers: List[Header] = []
    for h3 in content.find_all("h3"):
        if h3.text == "Getting updates":
            is_start = True
        if is_start:
            headers.append(
                Header(
                    name=h3.text,
                    anchor=h3.a["href"],
                    tag=h3,
                    components=parse_components(h3),
                )
            )
    # crete dict of objects {"#update": Component(name="Update"), ...}
    anchors: Dict[str, Component] = {
        c.anchor: c for h in headers for c in h.components if c.is_object
    }
    for h in headers:
        for c in h.components:
            parse_args(c, anchors)
            parse_subclasses(c, anchors)
            if c.is_path:
                parse_result(c, anchors)
    return headers


def get_api() -> Api:
    content = get_content()
    api = Api(version=parse_version(content), headers=parse_headers(content))
    process_input_media(api)
    for h in api.headers:
        for c in h.components:
            c.api = api
    return api
