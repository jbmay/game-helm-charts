"""Exercise the rendered downloader with a fake Mod Portal, without a cluster.

Run with: HELM=/path/to/helm python3 -m unittest discover -s charts/factorio/tests
"""

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import textwrap
import unittest


CHART = Path(__file__).resolve().parents[1]
HELM = shlex.split(os.environ.get("HELM", "helm"))


class ModDownloaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mods = self.root / "mods"
        self.mods.mkdir()
        releases = []
        for version, game in [("1.0.0", "2.1"), ("1.1.0", "2.1"),
                              ("1.2.0", "2.0"), ("1.3.0", "2.10")]:
            releases.append({
                "version": version,
                "info_json": {"factorio_version": game},
                "file_name": f"example_{version}.zip",
                "download_url": f"/download/{version}",
                "sha1": hashlib.sha1(f"payload:{version}".encode()).hexdigest(),
            })
        (self.root / "metadata.json").write_text(json.dumps({"releases": releases}))
        curl = self.root / "curl"
        curl.write_text(textwrap.dedent("""\
            #!/usr/bin/env python3
            import json, os, pathlib, sys
            args = sys.argv[1:]
            url = next(arg for arg in args if arg.startswith('https://'))
            if '/api/mods/' in url:
                data = json.loads(pathlib.Path(os.environ['FAKE_METADATA']).read_text())
                name = url.split('/api/mods/')[1].split('/')[0]
                data['name'] = name
                for release in data['releases']:
                    release['file_name'] = release['file_name'].replace('example_', name + '_')
                print(json.dumps(data))
            else:
                version = url.split('/download/')[1].split('?')[0]
                pathlib.Path(args[args.index('-o') + 1]).write_text('payload:' + version)
                print('200', end='')
            """))
        curl.chmod(0o755)

    def render(self, entries, **server):
        values = self.root / "values.json"
        values.write_text(json.dumps({
            "mods": {"enabled": True, "portal": entries},
            "factorioServer": server,
        }))
        return subprocess.run(
            HELM + ["template", "test", str(CHART), "-f", str(values)],
            text=True, capture_output=True,
        )

    def run_downloader(self, entries, **server):
        rendered = self.render(entries, **server)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        body = rendered.stdout.split("  mod-downloader.sh: |\n", 1)[1]
        lines = []
        for line in body.splitlines():
            if line and not line.startswith("    "):
                break
            lines.append(line[4:])
        script = "\n".join(lines).replace("modDir=/factorio/mods", f"modDir={shlex.quote(str(self.mods))}")
        return subprocess.run(
            ["bash", "-c", script], text=True, capture_output=True,
            env={**os.environ, "PATH": f"{self.root}:{os.environ['PATH']}",
                 "FAKE_METADATA": str(self.root / "metadata.json"),
                 "VERSION": "2.1.24", "USERNAME": "test", "TOKEN": "secret-test-token"},
        )

    def selected(self):
        return json.loads((self.mods / "mod-list.json").read_text())["mods"]

    def test_latest_string_and_object(self):
        for entry in ["example", {"name": "example"}]:
            with self.subTest(entry=entry):
                result = self.run_downloader([entry])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("version", self.selected()[0])
                self.assertTrue((self.mods / "example_1.1.0.zip").exists())
                self.assertNotIn("secret-test-token", result.stdout + result.stderr)

    def test_pin_overrides_existing_newer_version_and_preserves_other_entries(self):
        preserved = [{"name": "base", "enabled": True},
                     {"name": "quality", "enabled": False}]
        (self.mods / "mod-list.json").write_text(json.dumps({"mods": preserved + [
            {"name": "example", "enabled": False, "version": "1.1.0"}]}))
        (self.mods / "example_1.1.0.zip").write_text("existing newer zip")
        result = self.run_downloader([{"name": "example", "version": "1.0.0"}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.selected()[:2], preserved)
        self.assertEqual(self.selected()[2], {"name": "example", "enabled": True, "version": "1.0.0"})
        self.assertTrue((self.mods / "example_1.1.0.zip").exists())
        result = self.run_downloader(["example"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("version", self.selected()[2])
        self.assertTrue((self.mods / "example_1.1.0.zip").exists())

    def test_missing_and_incompatible_pins_fail_without_fallback(self):
        for version in ["9.9.9", "1.2.0", "1.3.0"]:
            with self.subTest(version=version):
                result = self.run_downloader([{"name": "example", "version": version}])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("No compatible release", result.stderr)
                self.assertFalse((self.mods / "mod-list.json").exists())

    def test_bad_checksum_fails_without_enabling_mod(self):
        metadata = self.root / "metadata.json"
        data = json.loads(metadata.read_text())
        data["releases"][0]["sha1"] = "0" * 40
        metadata.write_text(json.dumps(data))
        result = self.run_downloader([{"name": "example", "version": "1.0.0"}])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA1 mismatch", result.stderr)
        self.assertFalse((self.mods / "example_1.0.0.zip").exists())
        self.assertFalse((self.mods / "mod-list.json").exists())

    def test_empty_list(self):
        result = self.run_downloader([])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_pin_type_is_rejected(self):
        result = self.run_downloader([{"name": "example", "version": 123}])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mods.portal entries must", result.stderr)

    def test_updater_ignores_only_pinned_mods(self):
        entries = [{"name": "example", "version": "1.0.0"},
                   "latest-mod", {"name": "other-latest"},
                   {"name": "other-pin", "version": "1.0.0"}]
        rendered = self.render(entries, update_mods_on_start=True)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertIn('- name: UPDATE_MODS_ON_START\n          value: "true"', rendered.stdout)
        self.assertIn('- name: UPDATE_IGNORE\n          value: "example,other-pin"', rendered.stdout)
        result = self.run_downloader(entries, update_mods_on_start=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        mods = {mod["name"]: mod for mod in self.selected()}
        self.assertEqual(mods["example"]["version"], "1.0.0")
        self.assertEqual(mods["other-pin"]["version"], "1.0.0")
        self.assertNotIn("version", mods["latest-mod"])
        self.assertNotIn("version", mods["other-latest"])

    def test_updater_without_pins_has_no_ignore_list(self):
        rendered = self.render(["example", {"name": "latest-mod"}], update_mods_on_start=True)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertNotIn('- name: UPDATE_IGNORE', rendered.stdout)

    def test_removing_pin_clears_ignore_list(self):
        pinned = self.render([{"name": "example", "version": "1.0.0"}], update_mods_on_start=True)
        unpinned = self.render([{"name": "example"}], update_mods_on_start=True)
        self.assertIn('- name: UPDATE_IGNORE', pinned.stdout)
        self.assertNotIn('- name: UPDATE_IGNORE', unpinned.stdout)

    def test_mod_changes_trigger_rollout(self):
        first = self.render([{"name": "example", "version": "1.0.0"}])
        second = self.render([{"name": "example", "version": "1.1.0"}])
        def checksum(rendered):
            return next(line for line in rendered.stdout.splitlines() if "checksum/mod-downloader:" in line)
        self.assertNotEqual(checksum(first), checksum(second))


if __name__ == "__main__":
    unittest.main()
