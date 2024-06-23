import dataclasses
import warnings
from typing import Callable, ClassVar, Iterable, Optional, Sequence


@dataclasses.dataclass(frozen=True)
class MDConfig:
    """Configuration class for Markdown table parsing.

    This dataclass holds various configuration options that control how
    Markdown tables are parsed and formatted.

    Attributes:
        DEFAULT_TABLE_COL_SEP (ClassVar[str]): Default column separator.
        DEFAULT_TABLE_HDR_SEP (ClassVar[str]): Default header separator.
        sep (str): Column separator used in the table.
        header_sep (str): Character used for the header separator row.
        strict (bool): If True, applies stricter parsing rules.
        max_col_width (int): Maximum width for table columns.
        predicate (Callable[['Row'], bool]): Function to filter rows.
    """
    DEFAULT_TABLE_COL_SEP: ClassVar[str] = '|'
    DEFAULT_TABLE_HDR_SEP: ClassVar[str] = '-'

    sep: str = DEFAULT_TABLE_COL_SEP
    header_sep: str = DEFAULT_TABLE_HDR_SEP
    strict: bool = False
    max_col_width: int = 30
    predicate: Callable[['Row'], bool] = lambda _: True


class Row(dict[str, str]):
    """Represents a row in a Markdown table.

    This class extends the built-in dict to provide additional functionality
    specific to Markdown table rows.
    """
    @classmethod
    def genfromstr(cls, headers: Sequence[str],
                   line: str,
                   config: MDConfig = MDConfig(),
                   line_number: Optional[int] = None) -> 'Row':
        """Generate a Row object from a string line.

        Args:
            headers (Sequence[str]): The headers of the table.
            line (str): The string representation of the row.
            config (MDConfig, optional): Configuration for parsing.
            line_number (Optional[int]): Line number for error reporting.

        Returns:
            Row: A new Row object parsed from the input line.

        Raises:
            ValueError: If the line is not a valid row or if there are too many
                        columns.
        """
        if not cls.is_row(line, config=config):
            raise ValueError(f'Not a row: "{line}"')

        # Remove the first and last SEPARATOR chars (and whitespace)
        line = line.strip(config.sep).strip()

        # Split by separators to get column values
        values = line.split(config.sep)
        n_values = len(values)
        n_headers = len(headers)

        # More values than headers is an error, strict or not
        if n_values > n_headers:
            raise ValueError(
                f'Too many columns, expected {n_headers}, found {n_values}'
            )

        # Instantiate a row
        row = cls()

        # If some columns are missing, that is okay unless we're strict
        if n_values < n_headers:
            msg = 'Some columns are missing values.'

            # If strict, raise an error
            if config.strict:
                if line_number is not None:
                    msg += f' (line {line_number})'
                raise ValueError(msg)

            # If not strict, issue a warning and keep parsing
            msg += " Assuming they are empty."

            if line_number is not None:
                msg += f' (line {line_number})'

            warnings.warn(msg)

            # Set the missing column values to empty strings
            diff = n_headers - n_values
            for header in headers[-diff:]:
                row[header] = ''  # empty string

        # For the valid pairs of headers/values
        for header, value in zip(headers, values):
            row[header] = value.strip()

        return row

    @staticmethod
    def is_row(line: str, config: MDConfig = MDConfig()) -> bool:
        """Check if a given line is a valid table row.

        Args:
            line (str): The line to check.
            config (MDConfig, optional): Configuration for parsing.

        Returns:
            bool: True if the line is a valid row, False otherwise.
        """
        # slice(None, 1) -> first character
        # slice(-1, None) -> last character
        # This is better than using indexes as this would not raise an
        # index error given an empty string
        return line[:1] == line[-1:] == config.sep


class MarkDownTable(list[Row]):
    """Represents a Markdown table.

    This class provides methods for parsing, manipulating, and formatting
    Markdown tables.
    """

    def __init__(self, headers: Sequence[str], config: MDConfig = MDConfig()):
        self.headers: tuple[str, ...] = tuple(headers)
        # self.rows: list[Row] = list()
        self.config = config

    @staticmethod
    def get_headers(line: str,
                    config: MDConfig = MDConfig()) -> tuple[str, ...]:
        """
        Extract headers from a header line.

        Args:
            line (str): The header line to parse.
            config (MDConfig, optional): Configuration for parsing.

        Returns:
            tuple[str, ...]: A tuple of header strings.

        Raises:
            ValueError: If the header row is invalid.
        """
        # Remove the first and last SEPARATOR chars (and whitespace)
        line = line.strip(config.sep).strip()

        # Split by separators to get header values
        headers = line.split(config.sep)
        n_headers = len(headers)

        if n_headers < 1:
            raise ValueError('Invalid table header row')

        # No reason to allow headers to be mutable, so use a tuple
        return tuple(header.strip() for header in headers)

    @staticmethod
    def is_header_separator(line: str, config: MDConfig = MDConfig()) -> bool:
        """Check if a given line is a valid header separator.

        Args:
            line (str): The line to check.
            config (MDConfig, optional): Configuration for parsing.

        Returns:
            bool: True if the line is a valid header separator, False otherwise.
        """
        # Remove the first and last SEPARATOR chars (and whitespace)
        line = line.strip(config.sep).strip()

        # Just a
        # "---"
        # is a valid separator
        if line.startswith(config.header_sep):
            return True

        # Split by separators to get values
        vals = line.split(config.sep)

        if len(vals) < 1:
            return False

        return all(config.header_sep in val for val in vals)

    @classmethod
    def genfromtxt(cls, text: str,
                   headers: Optional[Sequence[str]] = None,
                   config: MDConfig = MDConfig()) -> 'MarkDownTable':
        """Generate a MarkDownTable instance from a text string.

        Args:
            text (str): The Markdown table text to parse.
            headers (Optional[Sequence[str]]): Table headers.
                If None, extracted from the text.
            config (MDConfig, optional): Configuration for parsing.

        Returns:
            MarkDownTable: A new MarkDownTable instance.

        Raises:
            ValueError: If the text cannot be parsed as a valid Markdown table.
        """
        # Ignore all surrounding whitespace
        text = text.strip()

        # Newlines begin new rows in the table
        # Use that to create an iterator over the lines
        lines = enumerate(line.strip() for line in text.splitlines())

        # If headers were not given, use the first line as the header row
        if headers is None:
            header_line: Optional[tuple[int, str]] = next(lines, None)
            if header_line is None:
                raise ValueError('The given text cannot be parsed as a table.')

            _, line = header_line
            headers = cls.get_headers(line, config=config)

        # Next line should be the header separator
        # We could ignore it, but verify it anyway
        sep_line = next(lines, None)
        if sep_line is None:
            raise ValueError(
                'Invalid markdown table.'
                'Found a header-like row, but then ran out of content'
            )

        num, line = sep_line

        if not cls.is_header_separator(line):
            raise ValueError(f'Expected separator row on line {num}')

        # Instantiate a table
        table = cls(headers, config=config)

        # Parse all remaining lines as table rows
        for num, line in lines:
            row = Row.genfromstr(headers=headers, line=line,
                                 config=config, line_number=num)
            if config.predicate(row):
                table.append(row)

        return table

    def append(self, row: Row) -> None:
        if not isinstance(row, Row):
            raise TypeError(f'Cannot append {type(row)}')

        row_headers = set(row.keys())
        our_headers = set(self.headers)

        if not our_headers.issuperset(row_headers):
            raise ValueError(
                f'Cannot add {row} because headers do not match {our_headers}'
            )

        for hdr in our_headers.difference(row_headers):
            row[hdr] = ''

        super().append(row)

    def extend(self, table: Iterable[Row]) -> None:
        if not isinstance(table, MarkDownTable):
            raise TypeError(f'Cannot extend {type(table)}')

        row_headers = set(table.headers)
        our_headers = set(self.headers)

        if not our_headers == row_headers:
            raise ValueError(
                f'Cannot add {table} because headers do not match {our_headers}'
            )

        super().extend(table)

    def copy(self) -> 'MarkDownTable':
        obj = MarkDownTable(self.headers, config=self.config)
        obj[:] = self[:]
        return obj

    def find(self,
             predicate: Callable[[Row], bool]) -> tuple[int, Optional[Row]]:
        def f(args: tuple[int, Row]) -> bool:
            # index, value = args
            return predicate(args[1])

        item = next(filter(f, enumerate(self)), None)

        if item is None:
            return (-1, None)

        return item

    def __add__(self, other: 'MarkDownTable') -> 'MarkDownTable':  # type: ignore[override]
        obj = self.copy()
        obj.extend(other)
        return obj

    def __str__(self):
        """Return a string representation of the table.

        Returns:
            str: A formatted string representation of the Markdown table.
        """
        return self.to_text(max_col_width=self.config.max_col_width,
                            justified=True)

    def __repr__(self):
        """Return a string representation of the MarkDownTable object.

        Returns:
            str: A string representation of the MarkDownTable instance.
        """
        headers = self.headers
        rows = self
        return f'MarkDownTable({headers=}, {len(rows)} Rows)'

    def to_text(self, max_col_width: Optional[int] = None,
                justified: bool = False) -> str:
        """
        Convert the table to a formatted text string.

        Args:
            max_col_width (Optional[int]): Maximum column width.
                If None, no limit is applied.
            justified (bool, optional): If True, left justify text in columns.

        Returns:
            str: A formatted string representation of the Markdown table.
        """
        headers = self.headers
        table = self

        string = ''

        def truncate(text: str, max_width: int) -> str:
            if len(text) > max_width:
                return text[:max_width - 3] + '...'
            else:
                return text

        # Calculate the maximum width for each column
        col_widths = {header: len(header) for header in headers}

        if max_col_width is not None:
            for row in table:
                for header in headers:
                    col_widths[header] = min(
                        max_col_width,
                        max(col_widths[header], len(row[header]))
                    )

        # Headers and separator line
        content: Iterable[str]
        if justified:
            content = (header.ljust(col_widths[header]) for header in headers)
        else:
            content = headers

        header_row = f' {self.config.sep} '.join(content)
        header_row = f'| {header_row} |'
        sep_row = ''.join(
            char if char == self.config.sep else self.config.header_sep
            for char in header_row
        )
        sep_row = f'{sep_row}'

        string += f"{header_row}\n{sep_row}\n"

        # Set all values to a very large number
        if max_col_width is None:
            col_widths = {header: 2 ** 32 for header in headers}

        # The rows
        for row in table:
            content = (truncate(row[hdr], col_widths[hdr]) for hdr in headers)

            if justified:
                zipped = zip(content, headers)
                content = map(lambda x: x[0].ljust(col_widths[x[1]]), zipped)

            row_str = ' | '.join(content)
            string += f'| {row_str} |\n'

        return string


text = '''
| Name       | Age | City       | Description |
| ---------------------------------------------------- |
| Alice      | 30  | New York   | Software Engineer... |
| Bob        | 25  | San Franc... | Data Scientist s... |
| Charlie    | 35  | London     | Product Manager w... |
'''

table = MarkDownTable.genfromtxt(text)

table.append(Row.genfromstr(
    headers=('Name', 'Age', 'City', 'Description'),
    line='| Duncan    | 18  | Berlin     | Student |'
))
