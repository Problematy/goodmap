# E2E Testing Suite for Goodmap

End-to-end testing infrastructure for the Goodmap application, validating the
backend and frontend together. This directory is part of the `goodmap`
monorepo (backend at the repo root, frontend in `../frontend`).

## Project Overview

This test suite verifies the functionality of the Goodmap application through
Playwright-based end-to-end tests written in Python.

## Prerequisites

- Python 3.10+
- Poetry (Python dependency management)
- Node.js (for the frontend dev server used during tests)

## Configuration

The test environment uses several configuration files:

- `e2e_test_config.yml`: Main configuration for the test instance
- `e2e_test_data.json`: Test data for the test suite
- `pyproject.toml`: Python dependencies and pytest configuration

## Getting Started

Run `poetry install` in this directory first.

### Basic E2E Tests

From the **repo root**, start each server in its own terminal, then run the tests in a third:

```bash
# Terminal 1
make run-e2e-backend

# Terminal 2
make run-frontend

# Terminal 3
make e2e-tests
```

`make e2e-tests` performs a single-shot check that both servers are reachable and aborts with a helpful message if either is missing.

### Stress Tests

1. Generate stress test data:
    ```bash
    make e2e-stress-tests-generate-data
    ```

2. Start the stress test environment:
    ```bash
    CONFIG_PATH=e2e_stress_test_config.yml GOODMAP_PATH=.. make run-e2e-env
    ```

3. Run stress tests (in a separate terminal):
    ```bash
    make e2e-stress-tests
    ```

### Running CI Locally

You can run the GitHub Actions workflow locally using [`act`](https://github.com/nektos/act).
The `.actrc` file in this directory pre-configures the runner image:

```bash
act -W ../.github/workflows/e2e-tests.yml
```

### Continuous Integration

These tests run automatically via `.github/workflows/e2e-tests.yml` at the
repo root, which checks out the backend, frontend, and this directory in one
go (they're all in the same repo) and runs the steps above. PR comments with
results are posted via `.github/workflows/pr-comment.yml` and
`.github/workflows/post-test-results.yml`, also at the repo root.

## Reusable Components

### Bash Scripts

#### Start Backend Script
`.github/scripts/start-backend.sh`

Starts the Goodmap backend with automatic health checking.

**Usage:**
```bash
start-backend.sh <log-file> <pid-file> <startup-wait-seconds> <command...>
```

**Parameters:**
- `log-file`: Path to store backend logs
- `pid-file`: Path to store backend PID
- `startup-wait-seconds`: Seconds to wait for startup (default: 5)
- `command...`: The complete command to run (can include environment variables and make targets)

#### Stop Backend Script
`.github/scripts/stop-backend.sh`

Gracefully stops the Goodmap backend.

**Usage:**
```bash
stop-backend.sh <pid-file> <config-pattern>
```

**Parameters:**
- `pid-file`: Path to the PID file
- `config-pattern`: Pattern to match flask process (e.g., `flask.*e2e_test_config`)

### Performance Summary Script

`.github/scripts/generate-perf-summary.js`

Generates performance summaries from stress test results. Supports both GitHub Step Summaries and PR comment formats.

**Usage:**
```bash
node .github/scripts/generate-perf-summary.js <perf-json-path> [--format=github|pr-comment]
```
