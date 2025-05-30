# Fac Ws Ai Multi Agent

A progressive, hands-on tutorial for building multi-agent code review systems using LangGraph architectural patterns.

## Quick Start

1. **Clone the repository**:

   - **with https:**

   ```bash
   git clone https://github.com/TandemCreativeDev/fac-ws_ai_multi-agent.git
   cd fac-ws_ai_multi-agent
   ```

   - **with ssh:**

   ```bash
   git clone git@github.com:TandemCreativeDev/fac-ws_ai_multi-agent.git
   cd fac-ws_ai_multi-agent
   ```

2. **Setup environment**

   ```bash
   conda env create -f environment.yml
   conda activate fac-ws_ai_multi-agent
   ```

## Project Structure

```
├── src/             # Code
├── environment.yml  # Conda environment
├── setup.cfg        # Tool configurations
└── pyproject.toml   # Build configuration
```

## Development

- **Code formatting**: `autopep8 --in-place --recursive src/`
- **Linting**: `flake8 src/`

## Git Branch Naming

Follow these conventions:

- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Critical fixes
- `chore/task-description` - Maintenance tasks
- `docs/documentation-update` - Documentation changes

## Commit Messages

Use conventional commits:

- `feat: add new feature`
- `fix: resolve bug`
- `docs: update documentation`
- `style: format code`
- `refactor: restructure code`
- `test: add tests`
- `chore: update dependencies`

## Author

[**TandemCreativeDev**](https://github.com/TandemCreativeDev) - hello@runintandem.com
