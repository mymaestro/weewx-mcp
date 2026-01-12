# Contributing to weewx-mcp

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/weewx-mcp.git
   cd weewx-mcp
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -e ".[dev,sse]"
   ```

## Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test thoroughly

3. **Follow code style**:
   - Run Black for formatting: `black weewx_mcp_server.py`
   - Run Flake8 for linting: `flake8 weewx_mcp_server.py`
   - Add type hints where possible

4. **Write clear commit messages**:
   ```
   Fix issue with temperature query on leap days
   
   - Add proper date validation
   - Update tests for edge cases
   - Update documentation
   ```

## Submitting Changes

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what changed and why
   - Any related issue numbers
   - Screenshots for UI changes (if applicable)

3. **Respond to review feedback** promptly and professionally

## Pull Request Guidelines

- One feature/fix per PR when possible
- Include tests for new functionality
- Update documentation as needed
- Update CHANGELOG.md
- Keep PRs focused and reasonably sized

## Reporting Issues

1. **Check existing issues** to avoid duplicates
2. **Use a clear, descriptive title**
3. **Provide detailed reproduction steps**
4. **Include your environment**:
   - Python version
   - WeeWX version
   - Operating system
   - MCP version

## Running Tests

```bash
pytest
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new methods
- Update CHANGELOG.md in the "Unreleased" section
- Follow existing documentation style

## Development Tips

- Test against real WeeWX databases when possible
- Consider both stdio and SSE transport paths
- Handle timezone-aware datetime conversions properly
- Provide helpful error messages

## Questions?

Open an issue with your question or discussion topic.

Thank you for contributing!
