from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from e2e_harness import runner


def build_manifest(enabled: bool) -> dict:
    return {
        'checks': {
            'build': enabled,
            'migration': False,
            'migrated_build': False,
        },
    }


def test_refresh_build_all_refreshes_every_enabled_case(monkeypatch, capsys) -> None:
    manifests = {
        'alpha': build_manifest(True),
        'disabled': build_manifest(False),
        'zeta': build_manifest(True),
    }
    refreshed: list[str] = []

    monkeypatch.setattr(runner, 'list_test_cases', lambda: list(manifests))
    monkeypatch.setattr(runner, 'load_test_case_manifest', manifests.__getitem__)
    monkeypatch.setattr(
        runner,
        'cmd_refresh_build_case',
        lambda _args, case_name: refreshed.append(case_name) or 0,
    )

    result = runner.cmd_refresh_build(runner.HarnessOptions(command='refresh-build', all=True))

    assert result == 0
    assert refreshed == ['alpha', 'zeta']
    output = capsys.readouterr().out
    assert 'Skipping test case disabled; build output checks are disabled.' in output
    assert 'Refreshed build goldens for 2 test case(s); skipped 1.' in output


def test_refresh_build_all_continues_after_case_failure(monkeypatch, capsys) -> None:
    case_names = ['alpha', 'beta', 'zeta']
    refreshed: list[str] = []

    monkeypatch.setattr(runner, 'list_test_cases', lambda: case_names)
    monkeypatch.setattr(runner, 'load_test_case_manifest', lambda _case_name: build_manifest(True))

    def refresh_case(_args, case_name: str) -> int:
        refreshed.append(case_name)
        return 1 if case_name == 'beta' else 0

    monkeypatch.setattr(runner, 'cmd_refresh_build_case', refresh_case)

    result = runner.cmd_refresh_build(runner.HarnessOptions(command='refresh-build', all=True))

    assert result == 1
    assert refreshed == case_names
    assert 'Build golden refresh failed for 1 of 3 test cases.' in capsys.readouterr().err


def test_refresh_build_all_reports_when_there_are_no_cases(monkeypatch, capsys) -> None:
    monkeypatch.setattr(runner, 'list_test_cases', lambda: [])

    result = runner.cmd_refresh_build(runner.HarnessOptions(command='refresh-build', all=True))

    assert result == 2
    assert f'No test cases found under {runner.TEST_CASES_ROOT}' in capsys.readouterr().err


def test_run_engine_script_detects_error_marker_on_stderr(monkeypatch, tmp_path: Path) -> None:
    script_path = tmp_path / 'comic_git_engine' / 'src' / 'build' / 'build_site.py'
    script_path.parent.mkdir(parents=True)
    script_path.write_text('', encoding='utf-8')
    completed = subprocess.CompletedProcess(
        args=['python', str(script_path)],
        returncode=0,
        stdout='',
        stderr='============= ERROR =============\nBuild failed\n',
    )
    monkeypatch.setattr(runner.subprocess, 'run', lambda *args, **kwargs: completed)

    with pytest.raises(RuntimeError, match='Engine build reported an error'):
        runner.run_engine_script(
            tmp_path,
            Path('src/build/build_site.py'),
            {},
            'python',
            'Engine build',
        )
