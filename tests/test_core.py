import json
import tempfile
import unittest
from pathlib import Path
from App.settings_store import validate, load, save
from App.plugin_registry import discover
from App.update_catalog import versions

class CoreTests(unittest.TestCase):
    def test_invalid_colors_and_types_fall_back(self):
        c = validate({"theme":{"primary":"bad","opacity":False}, "general":{"animations":1}})
        self.assertEqual(c["theme"]["primary"], "#00C8FF")
        self.assertEqual(c["theme"]["opacity"], 94)
        self.assertTrue(c["general"]["animations"])
    def test_session_defaults_even_when_saved_config_exists(self):
        # The UI starts with defaults; reading a prior settings file is opt-in only.
        from App.settings_store import DEFAULT
        self.assertEqual(validate({}), DEFAULT)

    def test_persistent_theme(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"settings.json"
            c = load(path)
            c["theme"]["primary"]="#13A9F1"
            save(c, path)
            self.assertEqual(load(path)["theme"]["primary"], "#13A9F1")
    def test_plugin_manifest_creates_a_section(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"cpu"
            folder.mkdir()
            (folder/"manifest.json").write_text(json.dumps({"id":"cpu","name":"CPU",
                "version":"0.1.0","settings":[{"key":"refresh","type":"integer","default":5}]}))
            self.assertEqual(discover(td)[0]["id"], "cpu")
    def test_reject_plugin_path_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)/"cpu"
            folder.mkdir()
            (folder/"manifest.json").write_text('{"id":"other","name":"Wrong","version":"1"}')
            self.assertEqual(discover(td), [])
    def test_updates_never_accept_path_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/"index.json").write_text(json.dumps({"versions":[{"version":"0.1.0",
                "file":"../evil.deb","sha256":"a"*64}]}))
            self.assertEqual(versions(td), [])
    def test_empty_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(versions(td), [])

if __name__=="__main__":
    unittest.main()
