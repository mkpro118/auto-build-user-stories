# User Story Generator

Automatically Build Markdown Tables from GitHub Issues

## Description

The User Story Generator is a Python-based tool designed to create and manage
user stories in a Markdown table format. It integrates with GitHub issues,
allowing you to easily track and update the status of user stories directly from
your command line.

## Features

- Create new user story entries from GitHub issues
- Update existing user story entries
- Parse and modify Markdown tables
- Extract content from specific markers in text
- Configurable logging levels

## Installation

To install the User Story Generator, you can use pip:

```bash
pip install git+https://github.com/mkpro118/auto-build-user-stories.git

# Or if you'd like a specific version
# pip install git+https://github.com/mkpro118/auto-build-user-stories.git@v1.0.0
```

## Usage

The User Story Generator can be used as a command-line tool with two main commands: `create` and `update`.

### Creating a New User Story

To create a new user story:

```bash
user_story --file path/to/your/file.md
           --skip-lines 2
           create \
           --issue-number 123 \
           --issue-html-url https://github.com/<username_or_org>/<repo>/issues/123 \
           --status "In Progress" \
           --content "Your user story content"
```

### Updating an Existing User Story

To update an existing user story:

```bash
user_story --file path/to/your/file.md
           --skip-lines 2
           update \
           --issue-number 123 \
           --status "Completed"
```

### Additional Options

- `--log-level`: Set the logging level (debug, info, warning, error, critical)
- `--skip-lines`: Number of lines to skip before parsing the user story table (default: 2)

## Development

### Requirements

- Python 3.9 or higher

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Mrigank Kumar [mkpro118@gmail.com](mailto:mkpro118@gmail.com)

## Links

- [GitHub Repository](https://github.com/mkpro118/auto-build-user-stories.git)
- [Issue Tracker](https://github.com/mkpro118/auto-build-user-stories/issues)
