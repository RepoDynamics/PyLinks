"""Create, modify and manage URLs."""


import urllib
import re


class URL:
    """A URL with a base address and optional queries."""

    def __init__(
            self, base: str,
            queries: dict[str, str] = None,
            fragment: str = None,
            query_delimiter: str = '&',
            quote_safe: str = ''
    ):
        """
        Parameters
        ----------
        base : str
            The base URL, e.g. 'https://example.com/index'.
            It must start with either 'https://' or 'http://'.
        queries : dict[str, str], optional
            Query fields as a dictionary of key-value pairs, e.g. `{'title': 'my-title'}`.
        """
        self.base, base_queries, base_fragment = self._process_url(base)
        self.queries = base_queries | queries if queries else base_queries
        self.fragment = fragment if fragment else base_fragment
        self.query_delimiter = query_delimiter
        self.quote_safe = quote_safe
        return

    def __str__(self):
        """The full URL, e.g. 'https://example.com/index?title=my-title&style=bold'"""
        url = self.base
        if self.query_string:
            url += f'?{self.query_string}'
        if self.fragment:
            url += f'#{self.fragment}'
        return url

    def __truediv__(self, path):
        if not isinstance(path, str):
            raise TypeError("Addition can only be performed on strings.")
        if path.startswith('/'):
            path = path[1:]
        if path.endswith('/'):
            path = path[:-1]
        return URL(
            base=f'{self.base}/{path}',
            queries=self.queries,
            fragment=self.fragment,
            query_delimiter=self.query_delimiter,
            quote_safe=self.quote_safe
        )

    def __repr__(self):
        repr = f'URL(base={self.base}'
        if self.queries:
            repr += f', queries={self.queries}'
        if self.fragment:
            repr += f', fragment={self.fragment}'
        return f'{repr})'

    def __copy__(self):
        return URL(
            base=self.base,
            queries=self.queries.copy(),
            fragment=self.fragment,
            query_delimiter=self.query_delimiter,
            quote_safe=self.quote_safe
        )

    @property
    def query_string(self) -> str:
        """The complete query string, e.g. 'title=my-title&style=bold'"""
        return self.query_delimiter.join(
            [
                f'{urllib.parse.quote(str(key), safe="")}={urllib.parse.quote(str(val), safe=self.quote_safe)}'
                for key, val in self.queries.items() if val is not None
            ]
        ) if self.queries else None

    def add_path(self, path: str):
        if path.startswith('/'):
            path = path[1:]
        if path.endswith('/'):
            path = path[:-1]
        self.base += f'/{path}'
        return

    def copy(self):
        return self.__copy__()

    @staticmethod
    def _process_url(url: str) -> tuple[str, dict[str, str], str]:
        """
        Process a URL and separate the base, query string and fragment.

        Parameters
        ----------
        url : str
            URL to process

        Returns
        -------
        base, queries, fragment : str, dict[str, str], str
        """

        def _process_query_string(query_string: str):
            queries = dict()
            for query in query_string.split('&'):
                key_val = query.split('=')
                if len(key_val) != 2:
                    raise ValueError("Query string not formatted correctly.")
                queries[key_val[0]] = key_val[1]
            return queries

        if not url.startswith(("http://", "https://")):
            raise ValueError("`base_url` must start with either 'http://' or 'https://'.")
        url_pattern = r"^(?P<base_url>[^?#]+)(?:\?(?P<query_string>[^#]+))?(?:#(?P<fragment>.*))?$"
        match = re.match(url_pattern, url)
        if not match:
            raise ValueError("URL not formatted correctly.")
        base_url = match.group('base_url')
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        query_string = match.group('query_string')
        fragment = match.group('fragment')
        queries = _process_query_string(query_string) if query_string else dict()
        return base_url, queries, fragment
