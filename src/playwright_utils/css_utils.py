"""CSS selector utilities for escaping and building selectors."""

# Translation table for escaping CSS class names.
# Characters that need escaping in CSS identifiers.
_CSS_ESCAPE_TABLE = str.maketrans({
    '\\': '\\\\',
    '[': '\\[',
    ']': '\\]',
    '(': '\\(',
    ')': '\\)',
    '{': '\\{',
    '}': '\\}',
    ':': '\\:',
    ';': '\\;',
    ',': '\\,',
    '.': '\\.',
    '!': '\\!',
    '@': '\\@',
    '#': '\\#',
    '$': '\\$',
    '%': '\\%',
    '^': '\\^',
    '&': '\\&',
    '*': '\\*',
    '+': '\\+',
    '=': '\\=',
    '|': '\\|',
    '/': '\\/',
    '~': '\\~',
    '`': '\\`',
    '"': '\\"',
    "'": "\\'",
    '<': '\\<',
    '>': '\\>',
    '?': '\\?',
    ' ': '\\ '
})


def escape_css_class(class_name: str) -> str:
    """Escape a CSS class name for use in selectors.

    Args:
        class_name: The class name to escape.

    Returns:
        Escaped class name safe for use in CSS selectors.
    """
    return class_name.translate(_CSS_ESCAPE_TABLE)


def build_css_selector(
    html_id: str = None,
    html_element: str = None,
    html_classes: str = None,
    fallback_tags: list[str] = None
) -> str:
    """Build a CSS selector from HTML attributes.

    Args:
        html_id: HTML ID attribute (highest priority).
        html_element: HTML element tag name.
        html_classes: Space-separated class names.
        fallback_tags: List of tag names to use if no element specified.

    Returns:
        Valid CSS selector string.
    """
    # Priority 1: Use ID selector (most specific).
    if html_id:
        selector = f"#{html_id}"
        if html_classes:
            classes = [f".{escape_css_class(cls)}" for cls in html_classes.split()]
            selector += ''.join(classes)
        return selector

    # Priority 2: Use element tag with classes.
    if html_element:
        selector = html_element
        if html_classes:
            classes = [f".{escape_css_class(cls)}" for cls in html_classes.split()]
            selector += ''.join(classes)
        return selector

    # Priority 3: Fallback to generic tags with classes applied to each.
    tags = fallback_tags or ["section", "header", "footer", "main", "nav", "aside", "article"]
    if html_classes:
        classes = [f".{escape_css_class(cls)}" for cls in html_classes.split()]
        class_str = ''.join(classes)
        return ','.join([f"{tag}{class_str}" for tag in tags])

    return ','.join(tags)

