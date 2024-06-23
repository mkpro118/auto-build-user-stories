import dataclasses
import enum
import re

from typing import ClassVar


@dataclasses.dataclass
class Config:
    class Defaults(enum.Enum):
        START_MARKER: ClassVar[str] = r'\s?### Description\s'
        END_MARKER: ClassVar[str] = r'\s###'
        CONTENT_PATTERN: ClassVar[str] = r'\s*\n\s*([\s\S]*?)\s*\n\s*'

    start_marker: str = Defaults.START_MARKER.value
    end_marker: str = Defaults.END_MARKER.value
    content_pattern: str = Defaults.CONTENT_PATTERN.value

    def __post_init__(self):
        self.pattern_str = ''.join((
            f'{self.start_marker}',
            f'{self.content_pattern}'
            f'{self.end_marker}',
        ))
        self.pattern = re.compile(self.pattern_str)


def extract_content(config: Config, text: str) -> str:
    pattern = config.pattern

    match = pattern.search(text)

    if match is None:
        raise ValueError('No match found')

    return match.group(1).strip()
