#!/usr/bin/env python

import yaml
import sys


class Tag:

    name = None

    def __init__(self, **attributes):
        self.attributes = attributes

        self.children = []

    def append(self, child):
        if type(child) == list:
            self.children.extend(child)
        else:
            self.children.append(child)

        return self

    def append_to(self, other):
        other.append(self)

        return self

    def prepend(self, child):
        self.children.insert(0, child)

        return self

    def __str__(self):
        tmpl = """<{name} {attributes}>{children}</{name}>"""
        tag_attrs = {}

        for name, value in self.attributes.items():
            used_name = name
            if name.endswith("_"):
                used_name = name[:-1]

            if type(value) == list:
                value = " ".join(value)

            tag_attrs[used_name] = value

        return tmpl.format(
            name=self.name,
            attributes=" ".join(['{}="{}"'.format(*p) for p in tag_attrs.items()]),
            children="".join(map(str, self.children)),
        )


class html(Tag):
    name = "html"
class head(Tag):
    name = "head"
class style(Tag):
    name = "style"
class title(Tag):
    name ="title"
class body(Tag):
    name="body"
class div(Tag):
    name = "div"
class table(Tag):
    name = "table"
class th(Tag):
    name = "th"
class tr(Tag):
    name = "tr"
class td(Tag):
    name = "td"


def render_outline(outline, settings):
    """ Renders outline according to settings

        Returns string with the resulting html.
    """

    table_tag = table()

    header = tr()
    table_tag.append(header)

    for column in settings["columns"]:
        column_name = column["name"]
        column_header = th()
        column_header.append(column_name)
        header.append(column_header)

    table_tag.append(render_outline_items(outline, settings))

    return table_tag


def render_outline_items(outline, settings, level=1):

    items = []

    def _render_item(title, attributes=None):
        """ Render an item

            Returns tag for item
        """
        table_row = tr(class_=["level%d" % level])

        cell = div(class_=[settings["columns"][0]["name"]])
        cell.append_to(td().append_to(table_row))

        marker = div(class_=["marker"])
        marker.append("&bull;")
        cell.append(marker)

        content = div(class_=["content"])
        cell.append(content)

        title_tag = div(class_=[settings["rows"][0]["name"]])
        title_tag.append(title)
        content.append(title_tag)

        if type(attributes) is dict:
            for row in settings["rows"][1:]:
                row_name = row["name"]

                element = div(class_=[row_name])
                content.append(element)

                if row_name in attributes:
                    element.append(attributes.get(row_name))

            for column in settings["columns"][1:]:
                column_name = column["name"]

                cell = td(class_=[column_name])
                table_row.append(cell)

                if column_name in attributes:
                    cell.append(attributes.get(column_name))

        return table_row

    for item in outline:
        if type(item) is dict:
            for title, attributes in item.items():

                table_row = _render_item(title, attributes)
                items.append(table_row)

                if type(attributes) is dict and "outline" in attributes:
                    items.extend(render_outline_items(attributes["outline"],
                                            settings, level+1))
        elif type(item) is str:
            table_row = _render_item(item)
            items.append(table_row)

    return items


def render_style(settings):
    """ Renders style in settings

        Returns string with css.
    """
    def collect_styles(item):
        styles = [":".join(s) + ";" for s in item["style"].items()]
        return "".join(styles)

    style_sheet = []
    for klass, items in settings.items():
        for item in items:
            if "style" in item and "name" in item:
                style_sheet.append("{selector} {{{styles}}}".format(
                    selector=".{name}".format(name=item["name"]),
                    styles=collect_styles(item),
                ))
    for level, item in enumerate(settings.get("levels", [])):
        if "style" in item:
                style_sheet.append("{selector} {{{styles}}}".format(
                    selector=".level{level}".format(level=level + 1),
                    styles=collect_styles(item),
                ))

    return "".join(style_sheet)


def render_outlines(documents):
    for document in documents:
        if ("columns" in document and "rows" in document and
            "levels" in document):
            settings = document
        else:
            outlines.append(document)


    # print(render_style(settings))

    content = body()

    scss = ""
    if "sass" in settings:
        source = settings["sass"]
        import sass
        scss = sass.compile(string=source)

    for outline in outlines:
        content.append(render_outline(outline, settings))

    html_document = html().append(
        head().append(
            style(type_="text/css").append(
                scss
            ).append(
                """
                body { margin: 0px; }
                .outline {
                display: -webkit-box;
                display: -moz-boz;
                display: -ms-flexbox;
                display: -webkit-flex;
                display: flex;
                flex-flow: row;
                }
                .marker {
                font-weight: bold;
                text-align: center;
                -webkit-flex: 0 0 20px;
                flex: 0 0 20px;
                }
                .content {
                -webkit-flex: 1 1 auto;
                flex: 1 1 auto;
                }
                """
            ).append(
                render_style(settings)
            )
        ).append(
            title().append("Outline")
        )
    ).append(
        content
    )

    return html_document

if "__main__" == __name__:
    documents = yaml.load_all(sys.stdin.read())
    settings = {}
    outlines = []





    print(html_document)
