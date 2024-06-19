"""
This type stub file was generated by pyright.
"""

from re import Pattern


def replace_colons(text: str, strip: bool = ...) -> str:
    """Parses a string with colon encoded emoji and renders found emoji.
    Unknown emoji are left as is unless `strip` is set to `True`

    :param text: String of text to parse and replace
    :param strip: Whether to strip unknown codes or to leave them as `:unknown:`

    >>> emoji_data_python.replace_colons('Hello world ! :wave::skin-tone-3: :earth_africa: :exclamation:')
    'Hello world ! 👋🏼 🌍 ❗'
    """
    ...

def get_emoji_regex() -> Pattern[str]: # -> Pattern[str]:
    """Returns a regex to match any emoji

    >>> emoji_data_python.get_emoji_regex().findall('Hello world ! 👋🏼 🌍 ❗')
    ['👋', '🏼', '🌍', '❗']
    """
    ...
