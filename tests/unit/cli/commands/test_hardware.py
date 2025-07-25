import argparse
from unittest.mock import MagicMock, patch

import pytest

from tinel.cli.commands.hardware import HardwareCommands


@pytest.fixture
def mock_formatter():
    return MagicMock()


@pytest.fixture
def mock_error_handler():
    handler = MagicMock()
    handler.handle_error.return_value = None
    return handler


@pytest.fixture
def hardware_cmd(mock_formatter, mock_error_handler):
    with (
        patch("tinel.cli.commands.hardware.AllHardwareToolProvider") as MockAll,
        patch("tinel.cli.commands.hardware.CPUInfoToolProvider") as MockCPU,
    ):
        mock_system = MagicMock()
        cmd = HardwareCommands(mock_formatter, mock_error_handler)
        cmd.system = mock_system
        cmd.all_hardware_tool = MockAll(cmd.system)
        cmd.cpu_tool = MockCPU(cmd.system)
        return cmd


@pytest.mark.parametrize("hardware_command", [None, "all"])
def test_show_all_hardware(hardware_cmd, mock_formatter, hardware_command):
    args = argparse.Namespace(
        hardware_command=hardware_command, detailed=True, summary=True
    )
    hardware_cmd.all_hardware_tool.run.return_value = {"hw": "all"}
    hardware_cmd._execute_tool = MagicMock(return_value={"hw": "all"})
    rc = hardware_cmd.execute(args)
    assert rc == 0
    mock_formatter.print_output.assert_called()


def test_show_cpu_info(hardware_cmd, mock_formatter):
    args = argparse.Namespace(
        hardware_command="cpu", detailed=True, temperature=True, features=True
    )
    hardware_cmd.cpu_tool.run.return_value = {"cpu": "info"}
    hardware_cmd._execute_tool = MagicMock(return_value={"cpu": "info"})
    rc = hardware_cmd.execute(args)
    assert rc == 0
    mock_formatter.print_output.assert_called()


def test_unknown_command(hardware_cmd, mock_error_handler):
    args = argparse.Namespace(hardware_command="unknown")
    rc = hardware_cmd.execute(args)
    assert rc == 1
    mock_error_handler.handle_error.assert_called_with(
        "Unknown hardware command: unknown"
    )


def test_show_all_hardware_exception(hardware_cmd):
    args = argparse.Namespace(hardware_command=None, detailed=False, summary=False)
    hardware_cmd._execute_tool = MagicMock(side_effect=Exception("fail"))
    hardware_cmd._handle_tool_error = MagicMock(return_value=99)
    rc = hardware_cmd._show_all_hardware(args)
    assert rc == 99
    hardware_cmd._handle_tool_error.assert_called()


def test_show_cpu_info_exception(hardware_cmd):
    args = argparse.Namespace(detailed=False, temperature=False, features=False)
    hardware_cmd._execute_tool = MagicMock(side_effect=Exception("fail"))
    hardware_cmd._handle_tool_error = MagicMock(return_value=77)
    rc = hardware_cmd._show_cpu_info(args)
    assert rc == 77
    hardware_cmd._handle_tool_error.assert_called()


def test_execute_main_exception(hardware_cmd):
    args = argparse.Namespace(
        hardware_command="cpu", detailed=False, temperature=False, features=False
    )
    hardware_cmd._show_cpu_info = MagicMock(side_effect=Exception("fail"))
    hardware_cmd._handle_tool_error = MagicMock(return_value=55)
    rc = hardware_cmd.execute(args)
    assert rc == 55
    hardware_cmd._handle_tool_error.assert_called()
