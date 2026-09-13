# Browser Fixtures

Each child directory is an independent mutable source fixture for opt-in browser
tests. The harness copies a fixture into a fresh temporary host repository for
every test. Browser behavior is asserted semantically and does not use goldens.
