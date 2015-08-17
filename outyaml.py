#!/Users/emieri/Documents/Projects/outyaml/virtualenvs/outyaml/bin/python
import yaml
import sys
import re

from collections import OrderedDict


class Duration:
    UNITS = OrderedDict((
        ("d", float(24 * 60 * 60)),
        ("h", float(60 * 60)),
        ("m", float(60)),
        ("s", float(1)),
    ))

    parse_re = re.compile(r"(?:\s*(?:\d+\.\d*[dhmsp]))*\s*")

    @classmethod
    def from_string(cls, string):
        duration = 0.0
        points = 0.0
        for fragment in string.split():
            unit = fragment[-1]
            value = float(fragment[:-1])
            if unit in Duration.UNITS:
                duration += value * Duration.UNITS[unit]
            elif "p" == unit:
                points += value

        return cls(duration=duration, points=points)

    def __init__(self, duration=0, points=0):
        self.duration = float(duration)
        self.points = float(points)

    def __str__(self):
        result = []
        if 0 < self.points:
            result.append("%.1fp" % self.points)
        duration = self.duration
        for unit, size in Duration.UNITS.items():
            if duration >= size:
                result.append("%d%s" % (int(duration / size), unit))
                duration = int(duration % size)

        return " ".join(result)

    def __bool__(self):
        return self.duration > 0 or self.points > 0

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented()

        result = self.__class__(
            duration=self.duration,
            points=self.points,
        )

        result.duration += other.duration
        result.points += other.points

        return result


class Estimate:
    #parser_re = re.compile(r"(?:\s*([+~-]?)(\d+[wdhmsp]))*")
    parser_re = re.compile(r"(?:[+~-]\((?=[^)]*\)))?(?:\d+\.?\d*[dhmsp]\s*)+\)?")

    @classmethod
    def from_string(cls, string):
        estimate = Estimate()
        for match in cls.parser_re.finditer(string):
            fragment = match.group(0)
            if "+" == fragment[0]:
                estimate.over = Duration.from_string(fragment[2:-1])
            elif "-" == fragment[0]:
                estimate.under = Duration.from_string(fragment[2:-1])
            elif "~" == fragment[0]:
                estimate.fudge = Duration.from_string(fragment[2:-1])
            else:
                estimate.duration = Duration.from_string(fragment)
        return estimate

    def __init__(self):
        self.duration = Duration()
        self.over = Duration()
        self.under = Duration()
        self.fudge = Duration()

    def __str__(self):
        result = []

        if self.duration:
            result.append(str(self.duration))

        if self.under:
            result.append("-(%s)" % (self.under))

        if self.over:
            result.append("+(%s)" % (self.over))

        if self.fudge:
            result.append("~(%s)" % (self.fudge))

        return " ".join(result)

    def __bool__(self):
        return bool(self.duration or self.under or
                self.over or self.fudge)

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented()

        result = self.__class__()

        result.duration = self.duration + other.duration
        result.over = self.over + other.over
        result.under = self.under + other.under
        result.fudge = self.fudge + other.fudge

        return result


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
class section(Tag):
    name = "section"
class p(Tag):
    name = "p"
class ul(Tag):
    name = "ul"
class li(Tag):
    name = "li"
class h6(Tag):
    name = "h6"


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
    settings = {}
    outlines = []
    for document in documents:
        if ("columns" in document and "rows" in document and
            "levels" in document):
            settings = document
        else:
            outlines.append(document)


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


def render_reports(documents):
    for document in documents:
        if type(document) is list:
            items = render_report_items(document, {}, level=3)
            for item in items:
                yield item


def render_report_items(document, settings, level=1):
    class header(Tag):
        name = "h%d" % level

    def _render_item(title, attributes):
        result = []
        h = header()
        h.append(title)
        result.append(h)

        if type(attributes) is dict:
            estimate = Estimate()
            if "tasks" in attributes:
                estimate = sum_estimate(attributes["tasks"], key="estimate", subkey="tasks")
            if not(estimate) and "estimate" in attributes:
                estimate = Estimate.from_string(attributes["estimate"])

            if estimate:
                estimate_element = div(class_="estimate")
                estimate_element.append("&nbsp;")
                estimate_element.append(str(estimate))
                estimate_element.append_to(h)

            if "description" in attributes:
                description = p(class_="description")
                description.append(attributes["description"])
                description

                result.append(description)

            if False and "notes" in attributes:
                notes = attributes["notes"]
                result.append(h6().append("Notes"))
                if type(notes) is list:
                    l = ul(class_="notes")
                    for item in notes:
                        li().append(item).append_to(l)
                    result.append(l)
                else:
                    result.append(p(class_="notes").append(notes))

            if "tasks" in attributes and attributes["tasks"]:
                result.extend(render_report_items(attributes["tasks"],
                                                  settings, level+1))

        return "".join(map(str, result))

    for epic in document:
        for title, attributes in epic.items():
            yield _render_item(title, attributes)


def sum_estimate(document, key="estimate", subkey="tasks"):
    estimates = []
    for epic in document:
        for title, attributes in epic.items():
            if type(attributes) is dict:
                sub_estimate = sum_estimate(attributes.get(subkey, []))
                if sub_estimate:
                    estimates.append(sub_estimate)
                elif key in attributes:
                    string = attributes[key]
                    estimates.append(Estimate.from_string(string))

    return sum(estimates, Estimate())


if "__main__" == __name__:
    documents = yaml.load_all(sys.stdin.read())

    html_document = "".join(map(str, render_reports(documents)))
    # for document in documents:
    #     print(sum_estimate(document, key="estimate"))

    print(html_document)
