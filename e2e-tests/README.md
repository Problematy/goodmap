# E2E Testing Suite for Goodmap

This repository contains end-to-end testing infrastructure for the Goodmap application, automating validation of both frontend and backend components.

## Project Overview

This test suite verifies the functionality of the Goodmap application through Cypress-based end-to-end tests. It sets up a complete testing environment with:

- Backend (Flask-based Goodmap application)
- Frontend (Goodmap frontend application)
- Caddy as a reverse proxy to handle routing between components

## Prerequisites

- Node.js and npm
- Python 3.10+
- Poetry (Python dependency management)
- Caddy server

## Configuration

The test environment uses several configuration files:

- `e2e_test_config.yml`: Main configuration for the test instance
- `e2e_test_data.json`: Test data for the test suite
- `cypress.config.js`: Cypress testing framework configuration
- `Caddyfile`: Caddy server configuration for proxying requests

## Getting Started

### Installation

1. Install Goodmap dependencies:
    ```bash
    make install-goodmap
    ```

### Running Tests
Basic E2E Tests
1. Start the Goodmap backend:

    ```bash
    make run-e2e-goodmap
    ```

2. Start the frontend server (in a separate terminal):
    ```bash
    cd goodmap-frontend && make serve
    ```

3. Start Caddy (in a separate terminal):
    ```bash
    caddy run
    ```

4. Run the tests:
    ```bash
    make e2e-tests
    ```

5. Stress Tests
Generate stress test data:
    ```bash
    make e2e-stress-tests-generate-data
    ```

6. Start the stress test environment:
    ```bash
    make run-e2e-stress-env
    ```

7. Run stress tests:
    ```bash
    make e2e-stress-tests
    ```

### Continuous Integration

The repository includes GitHub Actions workflows to automatically run the tests:

- `.github/workflows/test.yml`: Triggered on pull requests and pushes to main
- `.github/workflows/e2e-tests.yml`: Reusable workflow that can be called by other repositories
- `.github/workflows/pr-comment.yml`: Reusable workflow for posting test results to PRs
- `.github/workflows/post-results.yml`: Posts test results as PR comments when local tests complete

## Using as a Reusable Workflow

Other repositories (e.g., `goodmap`, `goodmap-frontend`) can trigger E2E tests by calling the reusable workflow:

```yaml
name: Run E2E Tests

on:
  pull_request:
  push:
    branches: [main]

jobs:
  e2e-tests:
    uses: problematy/goodmap-e2e-tests/.github/workflows/e2e-tests.yml@main
    permissions:
      contents: read
      pull-requests: write
    secrets: inherit
    with:
      # Version of goodmap to test (branch, tag, or SHA)
      goodmap-version: 'main'

      # Version of goodmap-frontend to test
      goodmap-frontend-version: 'main'

      # Which repository is calling (goodmap, goodmap-frontend, or goodmap-e2e-tests)
      calling-repo: 'goodmap'

      # Optional: Custom paths (defaults work for most cases)
      # e2e-tests-path: 'goodmap-e2e-tests'
      # goodmap-path: 'goodmap'
      # goodmap-frontend-path: 'goodmap-frontend'

      # Optional: Custom config file
      # goodmap-config-path: 'e2e_test_config.yml'
```

### Workflow Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `goodmap-version` | Yes | - | Git ref (branch/tag/SHA) of goodmap to test |
| `goodmap-frontend-version` | Yes | - | Git ref of goodmap-frontend to test |
| `calling-repo` | No | - | Repository calling the workflow (determines checkout behavior) |
| `e2e-tests-path` | No | `.` | Path where e2e-tests will be checked out |
| `goodmap-path` | No | `goodmap` | Path where goodmap will be checked out |
| `goodmap-frontend-path` | No | `goodmap-frontend` | Path where goodmap-frontend will be checked out |
| `goodmap-config-path` | No | `e2e_test_config.yml` | Config file for goodmap E2E tests |

**Note:** The workflow automatically detects which version of e2e-tests to use based on the `@ref` specified in the `uses:` statement. For example, if you call `uses: problematy/goodmap-e2e-tests/.github/workflows/e2e-tests.yml@changes2`, it will checkout the `changes2` branch. This also works with forks: `uses: raven-wing/goodmap-e2e-tests/.github/workflows/e2e-tests.yml@my-feature` will checkout from the fork.

### Example: Testing a goodmap PR

When a PR is created in the `goodmap` repository, automatically test it with the latest frontend:

```yaml
jobs:
  e2e-tests:
    uses: problematy/goodmap-e2e-tests/.github/workflows/e2e-tests.yml@main
    permissions:
      contents: read
      pull-requests: write
    secrets: inherit
    with:
      goodmap-version: ${{ github.sha }}          # Test this PR
      goodmap-frontend-version: 'main'             # Latest frontend
      calling-repo: 'goodmap'
      e2e-tests-path: 'goodmap-e2e-tests'          # Where e2e-tests will be checked out
      goodmap-path: '.'                            # Goodmap is already checked out here
```

### Example: Testing with a fork

If you want to test changes in your fork before merging:

```yaml
jobs:
  e2e-tests:
    uses: raven-wing/goodmap-e2e-tests/.github/workflows/e2e-tests.yml@changes2
    permissions:
      contents: read
      pull-requests: write
    secrets: inherit
    with:
      goodmap-version: ${{ github.sha }}
      goodmap-frontend-version: 'main'
      calling-repo: 'goodmap'
      e2e-tests-path: 'goodmap-e2e-tests'
      goodmap-path: '.'
```

The workflow will automatically checkout `changes2` from `raven-wing/goodmap-e2e-tests`.

## Reusable Components

### Path Handling for Cross-Repository Usage

When `e2e-tests.yml` is called from another repository, it automatically detects which repository and ref to checkout based on the `uses:` statement in the calling workflow. The workflow uses the GitHub API's `referenced_workflows` field to extract the repository and ref, ensuring it checks out the exact same version that contains the workflow file.

The workflow then uses the `e2e-tests-path` input parameter to correctly reference scripts. For example:

```bash
bash "${{ github.workspace }}/${{ inputs.e2e-tests-path }}/.github/scripts/start-backend.sh"
```

This ensures that resources are always loaded from the correct e2e-tests repository and version, regardless of which repository initiated the workflow.

### Bash Scripts

The repository provides reusable bash scripts for common tasks:

#### Start Backend Script
`.github/scripts/start-backend.sh`

Starts the Goodmap Flask backend with automatic health checking.

**Usage:**
```bash
start-backend.sh <config-path> <goodmap-path> <working-directory> <make-target> <log-file> <pid-file> [startup-wait-seconds]
```

**Parameters:**
- `config-path`: Path to Goodmap configuration file
- `goodmap-path`: Path to Goodmap repository
- `working-directory`: Working directory to run make from
- `make-target`: Make target to run (e.g., `run-e2e-env`)
- `log-file`: Path to store backend logs
- `pid-file`: Path to store backend PID
- `startup-wait-seconds`: Seconds to wait for startup (optional, default: 5)

**Example:**
```yaml
- name: Start backend
  run: |
    bash .github/scripts/start-backend.sh \
      "e2e_test_config.yml" \
      "${{ github.workspace }}/goodmap" \
      "goodmap" \
      "run-e2e-env" \
      "/tmp/backend.log" \
      "/tmp/backend.pid" \
      "5"
```

#### Stop Backend Script
`.github/scripts/stop-backend.sh`

Gracefully stops the Goodmap Flask backend.

**Usage:**
```bash
stop-backend.sh <pid-file> <config-pattern>
```

**Parameters:**
- `pid-file`: Path to the PID file
- `config-pattern`: Pattern to match flask process (e.g., `flask.*e2e_test_config`)

**Example:**
```yaml
- name: Stop backend
  if: always()
  run: |
    bash .github/scripts/stop-backend.sh \
      "/tmp/backend.pid" \
      "flask.*e2e_test_config"
```

### Performance Summary Script

`.github/scripts/generate-perf-summary.js`

Generates performance summaries from stress test results. Supports both GitHub Step Summaries and PR comment formats.

**Usage:**
```bash
node .github/scripts/generate-perf-summary.js <perf-json-path> [--format=github|pr-comment]
```

**Example:**
```yaml
- name: Add performance summary
  run: |
    node .github/scripts/generate-perf-summary.js \
      cypress/results/stress-test-perf.json \
      --format=github >> $GITHUB_STEP_SUMMARY
```

### PR Comment Workflows

The repository provides reusable workflows for posting E2E test results as PR comments:

#### `.github/workflows/pr-comment.yml` (Reusable Workflow)

Posts E2E test results to a pull request. This workflow can be called from any repository.

**Usage:**
```yaml
jobs:
  post-results:
    uses: problematy/goodmap-e2e-tests/.github/workflows/pr-comment.yml@main
    permissions:
      contents: read
      pull-requests: write
    secrets:
      comment_token: ${{ secrets.GITHUB_TOKEN }}
    with:
      run_id: ${{ github.event.workflow_run.id }}
```

**Inputs:**
- `run_id` (required): Workflow run ID to fetch artifacts from

**What it does:**
1. Downloads test result artifacts from the specified workflow run
2. Extracts PR metadata (PR number, commit SHA, e2e-tests path)
3. Generates performance summary using `generate-perf-summary.js`
4. Posts a comment to the PR with test results and performance metrics

#### `.github/workflows/post-results.yml` (Local Trigger)

Automatically posts test results when the "E2E Tests" workflow completes in this repository. This workflow watches for test completion and calls `pr-comment.yml`.

**Example for other repositories:**

In `goodmap` or `goodmap-frontend` repositories, create a similar workflow:

```yaml
name: Post E2E Test Results

on:
  workflow_run:
    workflows: ["Testing pipeline"]  # Name of your testing workflow
    types:
      - completed

permissions:
  contents: read
  pull-requests: write

jobs:
  post-results:
    uses: problematy/goodmap-e2e-tests/.github/workflows/pr-comment.yml@main
    permissions:
      contents: read
      pull-requests: write
    secrets:
      comment_token: ${{ secrets.GITHUB_TOKEN }}
    with:
      run_id: ${{ github.event.workflow_run.id }}
```


