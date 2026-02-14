#!/home/aipass/.venv/bin/python3

# ===================AIPASS====================
# META DATA HEADER
# Name: test_json_handler.py - Test JSON handler functions
# Date: 2026-02-11
# Version: 1.0.0
# Category: speakeasy/tests
#
# CHANGELOG (Max 5 entries):
#   - v1.0.0 (2026-02-11): Initial implementation
#
# CODE STANDARDS:
#   - Test file for speakeasy JSON handler
#   - Tests JSON file operations, template loading, validation
# =============================================

"""Tests for json_handler.py - JSON file management functions."""

import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime
import pytest

# Add apps directory to path so 'handlers' package resolves
sys.path.insert(0, str(Path(__file__).parent.parent / "apps"))

from handlers.json import json_handler


class TestLoadTemplate:
    """Tests for load_template function."""

    def test_loads_config_template(self, temp_test_dir):
        """Test loads config template successfully."""
        # Create template directory structure
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create config template
        config_template = {
            "module_name": "{{MODULE_NAME}}",
            "version": "1.0.0",
            "config": {
                "max_log_entries": 100
            }
        }

        template_path = template_dir / "config.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(config_template, f)

        # Patch JSON_TEMPLATES_DIR
        with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
            result = json_handler.load_template("config", "test_module")

        assert result["module_name"] == "test_module"
        assert result["version"] == "1.0.0"
        assert result["config"]["max_log_entries"] == 100

    def test_loads_data_template(self, temp_test_dir):
        """Test loads data template successfully."""
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        data_template = {
            "created": "2026-02-11",
            "last_updated": "2026-02-11"
        }

        template_path = template_dir / "data.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(data_template, f)

        with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
            result = json_handler.load_template("data", "test_module")

        assert "created" in result
        assert "last_updated" in result

    def test_loads_log_template(self, temp_test_dir):
        """Test loads log template successfully."""
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        log_template = []

        template_path = template_dir / "log.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(log_template, f)

        with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
            result = json_handler.load_template("log", "test_module")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_replaces_module_name_placeholder(self, temp_test_dir):
        """Test replaces {{MODULE_NAME}} placeholder."""
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        template = {
            "module": "{{MODULE_NAME}}",
            "path": "/home/{{MODULE_NAME}}/data"
        }

        template_path = template_dir / "config.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(template, f)

        with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
            result = json_handler.load_template("config", "speakeasy")

        assert result["module"] == "speakeasy"
        assert result["path"] == "/home/speakeasy/data"

    def test_raises_on_missing_template(self):
        """Test raises FileNotFoundError when template doesn't exist."""
        with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', Path("/nonexistent")):
            with pytest.raises(FileNotFoundError):
                json_handler.load_template("config", "test_module")


class TestValidateJsonStructure:
    """Tests for validate_json_structure function."""

    def test_validates_config_structure(self):
        """Test validates config JSON structure."""
        valid_config = {
            "module_name": "test",
            "version": "1.0.0",
            "config": {}
        }

        assert json_handler.validate_json_structure(valid_config, "config") is True

    def test_rejects_invalid_config_structure(self):
        """Test rejects invalid config structure."""
        invalid_config = {
            "module_name": "test"
            # Missing required keys
        }

        assert json_handler.validate_json_structure(invalid_config, "config") is False

    def test_rejects_non_dict_config(self):
        """Test rejects non-dict config."""
        assert json_handler.validate_json_structure([], "config") is False
        assert json_handler.validate_json_structure("string", "config") is False

    def test_validates_data_structure(self):
        """Test validates data JSON structure."""
        valid_data = {
            "created": "2026-02-11",
            "last_updated": "2026-02-11"
        }

        assert json_handler.validate_json_structure(valid_data, "data") is True

    def test_rejects_invalid_data_structure(self):
        """Test rejects invalid data structure."""
        invalid_data = {
            "created": "2026-02-11"
            # Missing last_updated
        }

        assert json_handler.validate_json_structure(invalid_data, "data") is False

    def test_validates_log_structure(self):
        """Test validates log JSON structure."""
        valid_log = []
        assert json_handler.validate_json_structure(valid_log, "log") is True

        valid_log_with_entries = [
            {"timestamp": "2026-02-11T10:00:00", "operation": "test"}
        ]
        assert json_handler.validate_json_structure(valid_log_with_entries, "log") is True

    def test_rejects_non_list_log(self):
        """Test rejects non-list log."""
        assert json_handler.validate_json_structure({}, "log") is False
        assert json_handler.validate_json_structure("string", "log") is False

    def test_unknown_json_type(self):
        """Test returns False for unknown JSON type."""
        assert json_handler.validate_json_structure({}, "unknown_type") is False


class TestGetJsonPath:
    """Tests for get_json_path function."""

    def test_returns_correct_path(self):
        """Test returns correct path for module JSON file."""
        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', Path("/test/dir")):
            result = json_handler.get_json_path("test_module", "config")
            assert result == Path("/test/dir/test_module_config.json")

    def test_different_json_types(self):
        """Test handles different JSON types."""
        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', Path("/test/dir")):
            config_path = json_handler.get_json_path("mymodule", "config")
            data_path = json_handler.get_json_path("mymodule", "data")
            log_path = json_handler.get_json_path("mymodule", "log")

            assert config_path.name == "mymodule_config.json"
            assert data_path.name == "mymodule_data.json"
            assert log_path.name == "mymodule_log.json"


class TestEnsureJsonExists:
    """Tests for ensure_json_exists function."""

    def test_creates_missing_json_file(self, temp_test_dir):
        """Test creates JSON file from template if missing."""
        json_dir = temp_test_dir / "json"
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create template
        template = {
            "module_name": "{{MODULE_NAME}}",
            "version": "1.0.0",
            "config": {}
        }
        with open(template_dir / "config.json", 'w') as f:
            json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.ensure_json_exists("test_module", "config")

        assert result is True
        json_file = json_dir / "test_module_config.json"
        assert json_file.exists()

    def test_preserves_existing_valid_file(self, temp_test_dir):
        """Test preserves existing valid JSON file."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()

        # Create existing valid file
        existing_data = {
            "module_name": "test",
            "version": "1.0.0",
            "config": {"key": "value"}
        }
        json_file = json_dir / "test_module_config.json"
        with open(json_file, 'w') as f:
            json.dump(existing_data, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            result = json_handler.ensure_json_exists("test_module", "config")

        assert result is True

        # Verify file wasn't modified
        with open(json_file, 'r') as f:
            loaded = json.load(f)
        assert loaded["config"]["key"] == "value"

    def test_regenerates_corrupted_file(self, temp_test_dir):
        """Test regenerates corrupted JSON file."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create corrupted file
        json_file = json_dir / "test_module_config.json"
        with open(json_file, 'w') as f:
            f.write("{invalid json")

        # Create template
        template = {
            "module_name": "{{MODULE_NAME}}",
            "version": "1.0.0",
            "config": {}
        }
        with open(template_dir / "config.json", 'w') as f:
            json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.ensure_json_exists("test_module", "config")

        assert result is True

        # Verify file was regenerated with valid JSON
        with open(json_file, 'r') as f:
            loaded = json.load(f)
        assert "module_name" in loaded

    def test_creates_directory_if_missing(self, temp_test_dir):
        """Test creates JSON directory if it doesn't exist."""
        json_dir = temp_test_dir / "json"
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # JSON dir doesn't exist yet
        assert not json_dir.exists()

        # Create template
        template = {"created": "2026-02-11", "last_updated": "2026-02-11"}
        with open(template_dir / "data.json", 'w') as f:
            json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.ensure_json_exists("test", "data")

        assert result is True
        assert json_dir.exists()


class TestLoadJson:
    """Tests for load_json function."""

    def test_loads_existing_json(self, temp_test_dir):
        """Test loads existing JSON file."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()

        data = {"key": "value", "number": 42}
        json_file = json_dir / "test_config.json"
        with open(json_file, 'w') as f:
            json.dump(data, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.ensure_json_exists', return_value=True):
                result = json_handler.load_json("test", "config")

        assert result == data

    def test_auto_creates_missing_json(self, temp_test_dir):
        """Test auto-creates JSON file if missing."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        template = {"module_name": "test", "version": "1.0.0", "config": {}}
        with open(template_dir / "config.json", 'w') as f:
            json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.load_json("test", "config")

        assert result is not None
        assert result["module_name"] == "test"


class TestSaveJson:
    """Tests for save_json function."""

    def test_saves_valid_json(self, temp_test_dir):
        """Test saves valid JSON to file."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()

        data = {
            "module_name": "test",
            "version": "1.0.0",
            "config": {"key": "value"}
        }

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            result = json_handler.save_json("test", "config", data)

        assert result is True

        # Verify file was written
        json_file = json_dir / "test_config.json"
        assert json_file.exists()

        with open(json_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == data

    def test_raises_on_invalid_structure(self, temp_test_dir):
        """Test raises ValueError on invalid structure."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()

        invalid_data = {"missing": "required_keys"}

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with pytest.raises(ValueError, match="Invalid structure"):
                json_handler.save_json("test", "config", invalid_data)

    def test_updates_last_updated_for_data_type(self, temp_test_dir):
        """Test updates last_updated timestamp for data JSON."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()

        data = {
            "created": "2026-01-01",
            "last_updated": "2026-01-01"
        }

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            json_handler.save_json("test", "data", data)

        # Verify last_updated was updated
        json_file = json_dir / "test_data.json"
        with open(json_file, 'r') as f:
            loaded = json.load(f)

        assert loaded["created"] == "2026-01-01"
        assert loaded["last_updated"] != "2026-01-01"  # Should be today's date


class TestLogOperation:
    """Tests for log_operation function."""

    def test_adds_log_entry(self, temp_test_dir):
        """Test adds entry to log file."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create templates
        for json_type in ["config", "data", "log"]:
            if json_type == "config":
                template = {"module_name": "test", "version": "1.0", "config": {"max_log_entries": 100}}
            elif json_type == "data":
                template = {"created": "2026-02-11", "last_updated": "2026-02-11"}
            else:
                template = []

            with open(template_dir / f"{json_type}.json", 'w') as f:
                json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.log_operation("test_operation", {"data": "value"}, "test")

        assert result is True

        # Verify log entry
        log_file = json_dir / "test_log.json"
        with open(log_file, 'r') as f:
            log = json.load(f)

        assert len(log) == 1
        assert log[0]["operation"] == "test_operation"
        assert log[0]["data"]["data"] == "value"
        assert "timestamp" in log[0]

    def test_rotates_log_when_exceeds_max(self, temp_test_dir):
        """Test rotates log entries when exceeding max_log_entries."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create templates with small max_log_entries
        config_template = {"module_name": "test", "version": "1.0", "config": {"max_log_entries": 3}}
        with open(template_dir / "config.json", 'w') as f:
            json.dump(config_template, f)

        data_template = {"created": "2026-02-11", "last_updated": "2026-02-11"}
        with open(template_dir / "data.json", 'w') as f:
            json.dump(data_template, f)

        log_template = []
        with open(template_dir / "log.json", 'w') as f:
            json.dump(log_template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                # Add 5 entries (should keep only last 3)
                for i in range(5):
                    json_handler.log_operation(f"operation_{i}", module_name="test")

        # Verify only 3 entries remain
        log_file = json_dir / "test_log.json"
        with open(log_file, 'r') as f:
            log = json.load(f)

        assert len(log) == 3
        assert log[0]["operation"] == "operation_2"
        assert log[2]["operation"] == "operation_4"


class TestIncrementCounter:
    """Tests for increment_counter function."""

    def test_increments_existing_counter(self, temp_test_dir):
        """Test increments existing counter."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create templates
        for json_type in ["config", "data", "log"]:
            if json_type == "config":
                template = {"module_name": "test", "version": "1.0", "config": {}}
            elif json_type == "data":
                template = {"created": "2026-02-11", "last_updated": "2026-02-11", "counter": 5}
            else:
                template = []

            with open(template_dir / f"{json_type}.json", 'w') as f:
                json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.increment_counter("test", "counter", 3)

        assert result is True

        # Verify counter was incremented
        data_file = json_dir / "test_data.json"
        with open(data_file, 'r') as f:
            data = json.load(f)

        assert data["counter"] == 8

    def test_creates_new_counter(self, temp_test_dir):
        """Test creates new counter if it doesn't exist."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create templates without counter
        for json_type in ["config", "data", "log"]:
            if json_type == "config":
                template = {"module_name": "test", "version": "1.0", "config": {}}
            elif json_type == "data":
                template = {"created": "2026-02-11", "last_updated": "2026-02-11"}
            else:
                template = []

            with open(template_dir / f"{json_type}.json", 'w') as f:
                json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.increment_counter("test", "new_counter", 1)

        assert result is True

        # Verify counter was created
        data_file = json_dir / "test_data.json"
        with open(data_file, 'r') as f:
            data = json.load(f)

        assert data["new_counter"] == 1


class TestUpdateDataMetrics:
    """Tests for update_data_metrics function."""

    def test_updates_metrics(self, temp_test_dir):
        """Test updates data metrics."""
        json_dir = temp_test_dir / "json"
        json_dir.mkdir()
        template_dir = temp_test_dir / "templates" / "default"
        template_dir.mkdir(parents=True)

        # Create templates
        for json_type in ["config", "data", "log"]:
            if json_type == "config":
                template = {"module_name": "test", "version": "1.0", "config": {}}
            elif json_type == "data":
                template = {"created": "2026-02-11", "last_updated": "2026-02-11"}
            else:
                template = []

            with open(template_dir / f"{json_type}.json", 'w') as f:
                json.dump(template, f)

        with patch('handlers.json.json_handler.SPEAKEASY_JSON_DIR', json_dir):
            with patch('handlers.json.json_handler.JSON_TEMPLATES_DIR', template_dir.parent):
                result = json_handler.update_data_metrics(
                    "test",
                    metric1="value1",
                    metric2=42,
                    metric3=True
                )

        assert result is True

        # Verify metrics were updated
        data_file = json_dir / "test_data.json"
        with open(data_file, 'r') as f:
            data = json.load(f)

        assert data["metric1"] == "value1"
        assert data["metric2"] == 42
        assert data["metric3"] is True
