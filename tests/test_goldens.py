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


def skip_if_disabled(case_name: str, is_enabled, label: str) -> None:
    manifest = runner.load_test_case_manifest(case_name)
    if not is_enabled(manifest):
        pytest.skip(f'{label} checks are disabled for {case_name}')


@pytest.mark.parametrize('case_name', CASE_NAMES, ids=CASE_NAMES)
def test_build_output_matches_golden(case_name: str) -> None:
    skip_if_disabled(case_name, runner.build_check_enabled, 'build output')

    result = runner.cmd_check_build_case(harness_args('check-build', case_name), case_name)

    assert result == 0


@pytest.mark.parametrize('case_name', CASE_NAMES, ids=CASE_NAMES)
def test_migration_output_matches_golden(case_name: str) -> None:
    skip_if_disabled(case_name, runner.migration_check_enabled, 'migration output')

    result = runner.cmd_check_migration_case(harness_args('check-migration', case_name), case_name)

    assert result == 0


@pytest.mark.parametrize('case_name', CASE_NAMES, ids=CASE_NAMES)
def test_migrated_build_output_matches_golden(case_name: str) -> None:
    skip_if_disabled(case_name, runner.migrated_build_check_enabled, 'migrated build output')

    result = runner.cmd_check_migrated_build_case(harness_args('check-migrated-build', case_name), case_name)

    assert result == 0
