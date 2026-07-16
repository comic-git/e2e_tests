from __future__ import annotations

import sys
from pathlib import Path

import pytest

from e2e_harness import runner


CASE_NAMES = runner.list_test_cases()

if not CASE_NAMES:
    pytest.skip(f'No test cases found under {runner.TEST_CASES_ROOT}', allow_module_level=True)


def harness_args(command: str, case_name: str) -> runner.HarnessOptions:
    python_executable = runner.DEFAULT_PYTHON if runner.DEFAULT_PYTHON.exists() else Path(sys.executable)
    return runner.HarnessOptions(
        command=command,
        case=case_name,
        python_executable=str(python_executable),
    )


def assert_check_passed(result: runner.CheckResult) -> None:
    if result.skipped:
        pytest.skip(result.message)
    detail = '\n'.join(result.differences)
    assert result.passed, f'{result.message}\n{detail}'


@pytest.mark.parametrize('case_name', CASE_NAMES, ids=CASE_NAMES)
def test_build_output_matches_golden(case_name: str) -> None:
    result = runner.check_build_case(harness_args('check-build', case_name), case_name)

    assert_check_passed(result)


@pytest.mark.parametrize('case_name', CASE_NAMES, ids=CASE_NAMES)
def test_migration_output_matches_golden(case_name: str) -> None:
    result = runner.check_migration_case(harness_args('check-migration', case_name), case_name)

    assert_check_passed(result)


@pytest.mark.parametrize('case_name', CASE_NAMES, ids=CASE_NAMES)
def test_migrated_build_output_matches_golden(case_name: str) -> None:
    result = runner.check_migrated_build_case(harness_args('check-migrated-build', case_name), case_name)

    assert_check_passed(result)
