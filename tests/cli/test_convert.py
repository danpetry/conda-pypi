import os
import sys

import pytest
from conda.cli.main import main_subshell


@pytest.mark.parametrize(
    "source, editable",
    [
        ("tests/packages/has-build-dep", False),
        ("tests/packages/has-build-dep", True),
    ],
)
def test_convert_writes_output(tmp_path, source, editable):
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    args = ["pypi", "convert", "--output-folder", str(out_dir)]
    if editable:
        args.append("-e")
    args.append(source)
    main_subshell(*args)

    files = list(out_dir.glob("*.conda"))
    assert files, f"No .conda artifacts found in {out_dir}"

    assert files[0].is_file()
    assert os.path.getsize(files[0]) > 0


def test_convert_wheel(tmp_path):
    """Test converting an existing wheel file to conda package."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    wheel_path = "tests/pypi_local_index/demo-package/demo_package-0.1.0-py3-none-any.whl"
    args = ["pypi", "convert", "--output-folder", str(out_dir), wheel_path]
    main_subshell(*args)

    files = list(out_dir.glob("*.conda"))
    assert files, f"No .conda artifacts found in {out_dir}"

    assert files[0].is_file()
    assert os.path.getsize(files[0]) > 0
    assert "demo-package" in files[0].name


def test_convert_wheel_with_tests(tmp_path, capsys):
    """Test converting an existing wheel file to conda package and injecting a test directory."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    test_dir = "tests/packages/has-test-dir/test"

    # Set platform-specific expected output
    if sys.platform == "win32":
        script_output = "run_test.bat present"
    else:
        script_output = "run_test.sh present"

    wheel_path = "tests/pypi_local_index/demo-package/demo_package-0.1.0-py3-none-any.whl"
    args = ["pypi", "convert", "--output-folder", str(out_dir), "--test-dir", test_dir, wheel_path]
    main_subshell(*args)

    files = list(out_dir.glob("*.conda"))
    assert files, f"No .conda artifacts found in {out_dir}"

    assert files[0].is_file()
    assert os.path.getsize(files[0]) > 0
    assert "demo-package" in files[0].name

    args = ["build", "-t", str(files[0])]
    print(args)
    main_subshell(*args)
    captured = capsys.readouterr()
    assert "run_test.py present" in captured.out
    assert script_output in captured.out
    assert "pip:" in captured.out


def test_convert_source_with_tests(tmp_path, capsys):
    """Test converting a source package to conda package and injecting a test directory."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    test_dir = "tests/packages/has-test-dir/test"

    # Set platform-specific expected output
    if sys.platform == "win32":
        script_output = "run_test.bat present"
    else:
        script_output = "run_test.sh present"

    source_path = "tests/packages/has-build-dep"
    args = ["pypi", "convert", "--output-folder", str(out_dir), "--test-dir", test_dir, source_path]
    main_subshell(*args)

    files = list(out_dir.glob("*.conda"))
    assert files, f"No .conda artifacts found in {out_dir}"

    assert files[0].is_file()
    assert os.path.getsize(files[0]) > 0

    args = ["build", "-t", str(files[0])]
    print(args)
    main_subshell(*args)
    captured = capsys.readouterr()
    assert "run_test.py present" in captured.out
    assert script_output in captured.out
    assert "pip:" in captured.out


def test_convert_with_invalid_test_dir(tmp_path):
    """Test that invalid test directory raises an appropriate error."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    nonexistent_dir = tmp_path / "nonexistent"

    wheel_path = "tests/pypi_local_index/demo-package/demo_package-0.1.0-py3-none-any.whl"
    args = ["pypi", "convert", "--output-folder", str(out_dir), "--test-dir", str(nonexistent_dir), wheel_path]

    with pytest.raises(FileNotFoundError, match="Test directory does not exist"):
        main_subshell(*args)


def test_convert_with_test_dir_missing_run_test(tmp_path):
    """Test that test directory without run_test.* file raises an error."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Create a file that doesn't match run_test.*
    with open(test_dir / "other_file.txt", 'w') as f:
        f.write("some content")

    wheel_path = "tests/pypi_local_index/demo-package/demo_package-0.1.0-py3-none-any.whl"
    args = ["pypi", "convert", "--output-folder", str(out_dir), "--test-dir", str(test_dir), wheel_path]

    with pytest.raises(ValueError, match="Test directory must contain at least one run_test"):
        main_subshell(*args)

