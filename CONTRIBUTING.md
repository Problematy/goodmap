# Contributor's Guideline

## Acceptance Criteria

- Test coverage must not decrease, and all tests must pass.
- The changelog must be updated.
- No breaking changes should be introduced (unless discussed otherwise). Use feature flags if needed.
- End-to-end tests must be added if a new feature is introduced.

## Rules

We keep our issues on GitHub fresh and clean. We put feature requests, bugs, and other tasks there. If you want to help develop our project, feel free to contribute!

There are plenty of issues reported on GitHub. Find one that suits you and make your change! Just remember that...

### Rule 1: Assign Yourself to an Issue

Choose an issue you want to work on and assign yourself to it. This helps other contributors know that someone is already working on it. Only assign yourself if you have time to resolve the issue. If we don't see any PRs from you for an extended period, you may be unassigned. You can reassign yourself when you have more time.

### Rule 2: Prioritize

Our backlog is diverse, with both cosmetic and functional changes. We try to prioritize them. Issues without a set priority may take longer to address.

To ensure your code is included in the next release, check if the issue has a milestone set and if it is the closest one.

### Rule 3: Test Your Changes

We write unit tests for our code, so ensure your code is tested.

### Rule 4: Don't Break It

If your PR does not pass our tests, it will not be merged. No one will review it until all tests pass.

## Exceptions

### Exception 1: Writing a Test

If your PR contains **only** tests that make our code more bug-resistant, you can treat it as if it has the highest priority.

## Development Setup

This repo is a monorepo: the Python/platzky backend lives at the root, the
React frontend in `frontend/`, and Playwright end-to-end tests in `e2e-tests/`.
Each has its own dependency manager and Makefile.

1. Use `poetry` to manage Python dependencies (backend and `e2e-tests/` each
   have their own `pyproject.toml` — run `poetry install` in both if you're
   touching e2e tests).
2. Run `npm install` inside `frontend/` if you're touching frontend code.
3. Before submitting a PR, run the linter for whatever you changed:
   - `make lint-check` (backend only), or
   - `make lint-check-all` to check backend, frontend, and e2e-tests together.
   - `make dev` runs `make lint-fix-all`, then `make lint-check-all` (including
     backend type-checking) and the backend unit tests — a one-shot local
     check-fix-and-test command.
4. Follow the repository's coding standards (e.g., line length of 100).

## Additional Notes

- Check the [GitHub Issues](https://github.com/Problematy/goodmap/issues) page to find tasks to work on.
- Use feature flags for introducing new functionality without breaking existing features.
- Ensure your PR adheres to the repository's style and testing guidelines.