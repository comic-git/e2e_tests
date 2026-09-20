from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from e2e_harness import cms_browser, runner


def pytest_addoption(parser) -> None:
    browser_group = parser.getgroup('comic_git browser tests')
    browser_group.addoption(
        '--decap-bundle',
        default=os.environ.get('COMIC_GIT_DECAP_BUNDLE'),
        help=(
            'Optional bundle file, bundle dist directory, or URL override for Decap CMS browser tests. '
            'By default, browser tests use the engine-generated vendored runtime.'
        ),
    )
    browser_group.addoption(
        '--keep-browser-temp',
        action='store_true',
        help='Keep browser-test temporary workspaces for debugging.',
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f'rep_{report.when}', report)


@pytest.fixture
def browser_harness_options(pytestconfig) -> cms_browser.BrowserHarnessOptions:
    python_executable = runner.DEFAULT_PYTHON if runner.DEFAULT_PYTHON.exists() else Path(sys.executable)
    return cms_browser.BrowserHarnessOptions(
        bundle_source=pytestconfig.getoption('--decap-bundle'),
        keep_temp=pytestconfig.getoption('--keep-browser-temp'),
        python_executable=str(python_executable),
    )
