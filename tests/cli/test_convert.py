import os

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
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    with open(test_dir / "run_test.py", 'w') as f:
        f.write("print(\"run_test.py present\")")
    with open(test_dir / "run_test.sh", 'w') as f:
        f.write("echo run_test.sh present")
    with open(test_dir / "test_time_dependencies.json", 'w') as f:
        f.write("[\n  \"pip\"\n]")

    wheel_path = "tests/pypi_local_index/demo-package/demo_package-0.1.0-py3-none-any.whl"
    args = ["pypi", "convert", "--output-folder", str(out_dir), "--test-dir", str(test_dir), wheel_path]
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
    assert "run_test.sh present" in captured.out
    assert "pip:" in captured.out

