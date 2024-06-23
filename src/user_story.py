import argparse
import datetime
import logging
import pathlib
import platform
import re
import sys

from typing import Callable

log = logging.getLogger(__name__)
logging.basicConfig()

try:
    from extract_content import extract_content, Config
    from parse_md_table import MarkDownTable, Row
except ImportError:
    parent = str(pathlib.Path(__file__).parent)

    log.info(f'Direct Imports failed! Adding parent "{parent}" to sys.path')

    sys.path.insert(0, parent)
    from extract_content import extract_content, Config
    from parse_md_table import MarkDownTable, Row


def add_create_args(create: argparse.ArgumentParser) -> None:
    # Add the --content flags
    create.add_argument('--content', '-c', type=str, required=True,
                        help='Content to build user story entry from')

    create.add_argument('--issue-number', '-n', type=int, required=True,
                        help='Related issue number')

    create.add_argument('--issue-html-url', '--url', type=str, default='',
                        help='URL to the related issue')

    create.add_argument('--status', '-s', type=str, required=True,
                        help='Status of the user story entry')


def add_update_args(update: argparse.ArgumentParser) -> None:
    # Add the --content flags
    update.add_argument('--issue-number', '-n', type=int, required=True,
                        help='Related issue number')

    update.add_argument('--status', '-s', type=str, required=True,
                        help='Status of the user story entry')


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    command_parser = parser.add_subparsers(
        dest='command',
        help='Action to perform',
        required=True
    )

    # Create subcommand
    create = command_parser.add_parser(
        'create',
        help='Create a new user story entry'
    )

    # Update subcommand
    update = command_parser.add_parser(
        'update',
        help='Update an existing user story entry'
    )

    add_create_args(create)
    add_update_args(update)

    # Common arguments
    # File to read/write
    parser.add_argument(
        '--file', '-f',
        type=pathlib.Path,
        default=pathlib.Path('docs/user-stories/README.md').resolve(),
        help='File to read from and add user story to'
    )

    # Skip lines (2 by default)
    parser.add_argument(
        '--skip-lines', '--skip',
        type=int,
        default=2,
        help='Number of lines to skip before parsing the user story table'
    )

    parser.add_argument(
        '--log-level', '-l',
        type=str.lower,
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='error',
        help='Set the logging level'
    )

    return parser.parse_args()


def read_file(filepath: str | pathlib.Path) -> str:
    log.debug(f'Reading file: "{filepath}"')
    with open(filepath) as f:
        content = f.read()

    return content


def write_file(filepath: str | pathlib.Path, content: str) -> None:
    log.debug(f'Writing {len(content)} bytes to file: "{filepath}"')

    with open(filepath, 'w+') as f:
        f.write(content)


def make_predicate(issue_number: int) -> Callable[[Row], bool]:
    log.debug(f'Making predicate for {issue_number = }')
    pattern = re.compile(r'\[#(\d+)\]')

    def predicate(row: Row) -> bool:
        match = pattern.match(row['Tracked by Issue'])

        if match is None:
            return False

        # Regex would have only selected digits
        # Should be a guaranteed cast
        return int(match.group(1)) == issue_number

    return predicate


def add_user_story(table: MarkDownTable,
                   description: str,
                   issue_number: int,
                   html_url: str,
                   status: str) -> MarkDownTable:
    predicate = make_predicate(issue_number)

    idx, row = table.find(predicate)

    if row is not None:
        new_table = MarkDownTable(headers=table.headers)
        new_table.append(row)

        text = new_table.to_text()

        log.error(f'Issue number {issue_number} already exists.\n{text}')
        sys.exit(1)

    # Collapse description into one line if it isn't already
    # Multiline text will break markdown tables
    description = ' '.join(
        desc if desc.endswith('.') else f'{desc}.'
        for desc in description.splitlines()
    )
    headers = table.headers

    fmt_str: str
    if platform.system() == 'Windows':
        fmt_str = '%e %b, %Y'
    else:
        fmt_str = '%-d %b, %Y'

    time_str = datetime.datetime.today().strftime(fmt_str)

    row_str = ' | '.join((
        description,
        time_str,
        f'[#{issue_number}]({html_url})' if html_url else f'#{issue_number}',
        status
    ))

    row_str = f'| {row_str} |'

    row = Row.genfromstr(headers=headers, line=row_str)
    table.append(row)

    return table


def update_user_story(table: MarkDownTable,
                      issue_number: int,
                      status: str) -> MarkDownTable:
    predicate = make_predicate(issue_number)
    idx, row = table.find(predicate)

    if row is None:
        log.error(f'No entry with issue number {issue_number} found')
        sys.exit(1)

    row['Status'] = status

    return table


def main():
    args = parse_arguments()
    log.setLevel(args.log_level.upper())

    log.debug(f'Using --log-level={args.log_level}')
    log.debug(f'Using --file="{args.file}"')
    log.debug(f'Using --skip-lines={args.skip_lines}')
    log.debug(f'Using command={args.command}')
    log.debug(f'Using --issue-number={args.issue_number}')
    log.debug(f'Using --status="{args.status}"')

    source = read_file(args.file)
    lines = source.splitlines()
    n_lines = len(lines)

    log.debug(f'Source contains {n_lines} lines.')
    log.debug(
        f'Table parser will use {n_lines - args.skip_lines} lines'
        f' (lines {args.skip_lines + 1}-{n_lines})'
    )

    keep = '\n'.join(lines[:args.skip_lines])
    table_str = '\n'.join(lines[args.skip_lines:])

    table = MarkDownTable.genfromtxt(table_str)
    log.debug(f'Parsed table\n    {table!r}')

    if args.command == 'create':
        log.debug(f'Using --issue-html-url={args.issue_html_url}')

        display_content = args.content
        max_display_length = 16
        content_length = len(display_content)
        if content_length > max_display_length:
            display_content = f'{display_content[:16]}...'

        display_content = '\\n'.join(display_content.splitlines())

        log.debug(
            f'Using --content="{display_content}" ({content_length} bytes total)'
        )

        content = args.content
        config = Config()
        try:
            description = extract_content(config=config, text=content)
        except ValueError:
            msg = 'Could not parse description from content.'
            if args.log_level != 'debug':
                msg += ' Use `--log-level=debug` to see additional details'

            log.error(msg)

            log.debug(f'Using start_marker="{config.start_marker}"')
            log.debug(f'Using end_marker="{config.end_marker}"')
            log.debug(f'Content:\n"{content}"')
            sys.exit(1)
        assert description is not None, 'Description is not available'

        add_user_story(
            table=table,
            description=description,
            issue_number=args.issue_number,
            html_url=args.issue_html_url,
            status=args.status
        )
    elif args.command == 'update':
        update_user_story(
            table=table,
            issue_number=args.issue_number,
            status=args.status
        )

    table_str = table.to_text()

    write_file(args.file, f'{keep}\n{table_str}')

    if args.command == 'create':
        print('\nCreated User Story successsully!')
    elif args.command == 'update':
        print('\nUpdated User Story successsully!')

    sys.exit(0)


if __name__ == '__main__':
    main()
