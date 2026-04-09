"""Tests for license file handling in conda package builds."""

from pathlib import Path

from conda_pypi.build import get_license_files, copy_licenses_to_info


class TestGetLicenseFiles:
    """Tests for get_license_files() function."""

    def test_with_license_file_metadata_pep639(self, tmp_path: Path):
        """License-File entries in METADATA point to dist-info/licenses/ (PEP 639)."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.1\n"
            "Name: pkg\n"
            "Version: 1.0\n"
            "License-File: LICENSE\n"
            "License-File: NOTICE\n"
        )
        licenses_dir = dist_info / "licenses"
        licenses_dir.mkdir()
        (licenses_dir / "LICENSE").write_text("MIT License")
        (licenses_dir / "NOTICE").write_text("Copyright notice")

        result = get_license_files(dist_info)

        assert len(result) == 2
        assert {f.name for f in result} == {"LICENSE", "NOTICE"}

    def test_with_license_file_metadata_old_layout(self, tmp_path: Path):
        """License-File entries point directly to dist-info/ (older wheels)."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\nLicense-File: LICENSE.txt\n"
        )
        (dist_info / "LICENSE.txt").write_text("BSD License")

        result = get_license_files(dist_info)

        assert len(result) == 1
        assert result[0].name == "LICENSE.txt"

    def test_fallback_to_licenses_dir(self, tmp_path: Path):
        """When no License-File in METADATA, check dist-info/licenses/."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n")
        licenses_dir = dist_info / "licenses"
        licenses_dir.mkdir()
        (licenses_dir / "LICENSE").write_text("Apache License")

        result = get_license_files(dist_info)

        assert len(result) == 1
        assert result[0].name == "LICENSE"

    def test_fallback_to_common_patterns(self, tmp_path: Path):
        """When no License-File or licenses dir, search for common patterns."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n")
        (dist_info / "LICENSE").write_text("GPL License")
        (dist_info / "COPYING.txt").write_text("Copying info")

        result = get_license_files(dist_info)

        assert len(result) == 2
        assert {f.name for f in result} == {"LICENSE", "COPYING.txt"}

    def test_no_license_files_found(self, tmp_path: Path):
        """Returns empty list when no license files exist."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n")

        result = get_license_files(dist_info)

        assert result == []

    def test_missing_license_file_logs_warning(self, tmp_path: Path, caplog):
        """Logs warning when License-File entry points to missing file."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\nLicense-File: MISSING_LICENSE\n"
        )

        result = get_license_files(dist_info)

        assert result == []
        assert "MISSING_LICENSE" in caplog.text
        assert "not found" in caplog.text


class TestCopyLicensesToInfo:
    """Tests for copy_licenses_to_info() function."""

    def test_copies_license_files_to_info_licenses(self, tmp_path: Path):
        """License files are copied to info/licenses/ per CEP 34."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\nLicense-File: LICENSE\n"
        )
        licenses_dir = dist_info / "licenses"
        licenses_dir.mkdir()
        (licenses_dir / "LICENSE").write_text("MIT License content")

        info_path = tmp_path / "info"
        info_path.mkdir()

        copied = copy_licenses_to_info(dist_info, info_path)

        assert copied == ["LICENSE"]
        assert (info_path / "licenses" / "LICENSE").exists()
        assert (info_path / "licenses" / "LICENSE").read_text() == "MIT License content"

    def test_copies_multiple_license_files(self, tmp_path: Path):
        """Multiple license files are all copied."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n"
            "License-File: LICENSE\nLicense-File: NOTICE\n"
        )
        licenses_dir = dist_info / "licenses"
        licenses_dir.mkdir()
        (licenses_dir / "LICENSE").write_text("MIT")
        (licenses_dir / "NOTICE").write_text("Notice text")

        info_path = tmp_path / "info"
        info_path.mkdir()

        copied = copy_licenses_to_info(dist_info, info_path)

        assert set(copied) == {"LICENSE", "NOTICE"}
        assert (info_path / "licenses" / "LICENSE").exists()
        assert (info_path / "licenses" / "NOTICE").exists()

    def test_returns_empty_when_no_licenses(self, tmp_path: Path):
        """Returns empty list when no license files exist."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n")

        info_path = tmp_path / "info"
        info_path.mkdir()

        copied = copy_licenses_to_info(dist_info, info_path)

        assert copied == []
        assert not (info_path / "licenses").exists()

    def test_creates_licenses_dir_if_missing(self, tmp_path: Path):
        """Creates info/licenses/ directory if it doesn't exist."""
        dist_info = tmp_path / "pkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n")
        (dist_info / "LICENSE").write_text("License text")

        info_path = tmp_path / "info"
        info_path.mkdir()

        copy_licenses_to_info(dist_info, info_path)

        assert (info_path / "licenses").is_dir()
