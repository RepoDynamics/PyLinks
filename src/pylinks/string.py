import re as _re
import unicodedata as _unicodedata


def to_slug(string: str) -> str:
    """Convert a string to a URL-friendly slug.

    This function performs unicode-normalization on the string,
    converts it to lowercase,
    replaces any non-alphanumeric characters with hyphens, and
    removes leading and trailing hyphens.
    """
    # Normalize the string to decompose special characters
    normalized_string = _unicodedata.normalize('NFKD', string)
    # Encode the string to ASCII bytes, ignoring non-ASCII characters
    ascii_bytes = normalized_string.encode('ascii', 'ignore')
    # Decode back to a string
    ascii_string = ascii_bytes.decode('ascii')
    lower_case_string = ascii_string.lower()
    return _re.sub(r'[^a-z0-9]+', '-', lower_case_string).strip('-')


def camel_to_title(string: str) -> str:
    """Convert a 'CamelCase' string to a 'Title Case' string.

    This function inserts spaces before each uppercase letter (except the first letter)
    and capitalizes the first letter of each word.
    """
    # Insert spaces before each uppercase letter (except the first letter)
    spaced_str = _re.sub(r'(?<!^)(?=[A-Z])', ' ', string)
    # Convert to title-case
    title_str = spaced_str.title()
    return title_str


def snake_to_camel(string):
    components = string.split('_')
    return ''.join([components[0]] + [x.title() for x in components[1:]])

