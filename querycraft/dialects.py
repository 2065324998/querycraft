"""SQL dialect configuration for different database backends."""

from dataclasses import dataclass


@dataclass
class Dialect:
    """SQL dialect configuration."""
    name: str
    placeholder: str = "?"
    quote_char: str = '"'
    supports_limit_offset: bool = True
    supports_returning: bool = False

    def quote_identifier(self, name):
        """Quote a table or column identifier."""
        if '.' in name:
            parts = name.split('.', 1)
            return (f"{self.quote_char}{parts[0]}{self.quote_char}"
                    f".{self.quote_char}{parts[1]}{self.quote_char}")
        return f"{self.quote_char}{name}{self.quote_char}"


SQLITE = Dialect(name="sqlite", placeholder="?")
MYSQL = Dialect(name="mysql", placeholder="%s", quote_char="`")
POSTGRESQL = Dialect(name="postgresql", placeholder="%s",
                     supports_returning=True)
