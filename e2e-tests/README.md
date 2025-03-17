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
- `.github/workflows/test-base.yml`: Base workflow called by test.yml


