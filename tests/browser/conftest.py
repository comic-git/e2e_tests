from __future__ import annotations

from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, sync_playwright

from e2e_harness import cms_browser


@dataclass
class CmsBrowserSession:
    harness: cms_browser.CmsBrowserHarness
    page: Page


@pytest.fixture
def cms_session(request, browser_harness_options) -> CmsBrowserSession:
    fixture = cms_browser.load_browser_fixture()
    with cms_browser.CmsBrowserHarness(fixture, browser_harness_options) as harness:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            console_messages: list[str] = []
            page.on('console', lambda message: console_messages.append(f'{message.type}: {message.text}'))
            page.on('pageerror', lambda error: console_messages.append(f'pageerror: {error}'))
            try:
                yield CmsBrowserSession(harness, page)
            finally:
                report = getattr(request.node, 'rep_call', None)
                if report is not None and report.failed:
                    try:
                        artifact_dir = harness.capture_artifacts(request.node.nodeid, page, console_messages)
                        print(f'Browser failure artifacts: {artifact_dir}')
                    except Exception as error:
                        print(f'Could not capture browser failure artifacts: {error}')
                browser.close()
