"""Shared page skeleton. Spec: docs/design/ui-proposal.md, Global elements."""

from dash import dcc, html


def page(strip, main, side=None, tabs=None):
    row = [html.Main(main, className="ui-main")]
    if side is not None:
        row.append(html.Aside(side, className="ui-side"))
    children = [strip, html.Div(row, className="ui-main-row")]
    if tabs is not None:
        children.append(tabs)
    return html.Div(children, className="ui-page")


def key_strip(items):
    """Items contain label, value, optional sign (green/red), and tooltip."""
    return html.Div(
        [
            html.Div(
                [
                    html.Div(item["label"], className="ui-key-label"),
                    html.Div(
                        item["value"],
                        className="ui-key-value"
                        + (f" ui-{item['sign']}" if item.get("sign") in ("green", "red") else ""),
                    ),
                ],
                title=item.get("tooltip", ""),
            )
            for item in items
        ],
        className="ui-key-strip",
    )


def details(summary, children):
    return html.Details([html.Summary(summary), children], open=False, className="ui-details")


def info(text):
    return html.Span("i", title=text, className="ui-info", tabIndex=0)


def tabs_below(children, **kwargs):
    for child in children:
        if isinstance(child, dcc.Tab):
            child.className = "ui-tab"
            child.selected_className = "ui-tab ui-tab-selected"
    return dcc.Tabs(children=children, className="ui-tabs", **kwargs)
