from tests.utils import create_mock_config_file
from tinel.tools.kernel_tools import run_kernel_config_check


def test_end_to_end():
    config_content = """
CONFIG_SECURITY_SELINUX=n
CONFIG_HUGETLBFS=n
"""
    path = create_mock_config_file(config_content, gzipped=True)
    result = run_kernel_config_check(path)
    assert result["config"] is not None
    assert len(result["issues"]) > 0
    assert len(result["recommendations"]) > 0
    assert result["error"] is None


def test_run_kernel_config_check_error():
    path = "non_existent_file"
    result = run_kernel_config_check(path)
    assert result["error"] is not None
