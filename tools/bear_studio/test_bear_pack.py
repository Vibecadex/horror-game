"""Team bear-pack compatibility and preservation across real catalogue imports."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import bear_pack
import server
from test_server import glb


def fixture(version=10, report=None, model_name='model.glb'):
    files = {model_name: glb(), 'report.json': json.dumps(report or {'status': 'warn', 'checks': []}).encode(),
             'landmarks.json': b'{"complete":false,"missing":["head"],"problems":["no head found"]}'}
    entries = {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in files.items()}
    revision = hashlib.sha256('\n'.join(f"{name} {entries[name]['sha256']}" for name in sorted(entries)).encode()).hexdigest()[:32]
    doc = {'format': 'bear-pack', 'formatVersion': 1, 'id': 'team-bear', 'name': 'Team bear', 'version': version,
           'revision': revision, 'model': {'file': model_name}, 'report': {'file': 'report.json'},
           'landmarks': {'file': 'landmarks.json', 'complete': False, 'missing': ['head'], 'problems': ['no head found']},
           'coordinates': {'units': 'meters', 'handedness': 'right', 'up': '+Y', 'front': '+Z'},
           'capture': {'pose': 'animation'}, 'files': entries}
    return doc, files


def zipped(doc, files, extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('Bear_team-bear/manifest.json', json.dumps(doc))
        for name, data in files.items():
            archive.writestr('Bear_team-bear/' + name, data)
        if extra:
            archive.writestr(*extra)
    return stream.getvalue()


class PackTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.store = server.Store(Path(self.scratch.name), seed=False)

    def test_offline_pack_keeps_landmarks_hashes_and_survives_restart(self):
        doc, files = fixture(model_name='Rupert.glb')
        data = zipped(doc, files)
        result = self.store.import_pack('Rupert.zip', data)
        bear = result['bear']
        self.assertEqual(bear['source']['pack']['capture']['pose'], 'animation')
        self.assertEqual(bear['source']['pack']['landmarks']['missing'], ['head'])
        self.assertEqual(self.store.asset(bear['modelUrl']).read_bytes(), files['Rupert.glb'])
        url = bear['modelUrl'].replace('model.glb', 'landmarks.json')
        self.assertEqual(self.store.asset(url).read_bytes(), files['landmarks.json'])
        self.assertFalse(self.store.import_pack('Renamed.zip', data)['imported'])
        self.assertEqual(server.Store(Path(self.scratch.name), seed=False).detail(bear['id']), bear)

    def test_tampered_sidecar_and_model_are_refused_before_catalogue_write(self):
        for name in ('model.glb', 'landmarks.json'):
            doc, files = fixture()
            files[name] = b'x' + files[name][1:]
            with self.assertRaisesRegex(server.APIError, 'does not match'):
                self.store.import_pack('Broken.zip', zipped(doc, files))
        self.assertEqual(self.store.list(), [])

    def test_reports_only_update_preserves_old_source_and_invalidates_old_rig(self):
        doc, files = fixture()
        first = self.store.import_pack('Bear.zip', zipped(doc, files))['bear']
        import base64
        rig = self.store.add_rig(first['id'], {'sourceRevision': 1, 'sourceSha256': first['sourceSha256'],
                  'recipe': {}, 'validation': {}, 'glbBase64': base64.b64encode(glb(True)).decode()})
        doc2, files2 = fixture(version=11, report={'status': 'fail', 'checks': [{'id': 'props', 'status': 'fail'}]})
        new = self.store.import_pack('Bear.zip', zipped(doc2, files2))['bear']
        self.assertEqual(new['id'], first['id'])
        self.assertEqual(new['sourceRevision'], 2)
        self.assertEqual(new['sourceSha256'], first['sourceSha256'])
        self.assertTrue(new['rigs'][0]['stale'])
        self.assertEqual(new['sourceReport']['status'], 'fail')
        self.assertEqual(self.store.asset(first['modelUrl']).read_bytes(), files['model.glb'])
        with self.assertRaisesRegex(server.APIError, 'older bear pack'):
            self.store.import_pack('Old.zip', zipped(doc, files))
        self.assertEqual(self.store.detail(first['id'])['sourceRevision'], 2)

    def test_unknown_format_wrong_axes_and_unsafe_model_name_are_refused(self):
        original, files = fixture()
        for field, value in [('formatVersion', 2), ('formatVersion', True), ('coordinates', {'up': '+Z'}), ('model', {'file': '../model.glb'}), ('model', {'file': []}), ('landmarks', {'file': {}})]:
            doc = copy.deepcopy(original)
            doc[field] = value
            with self.assertRaises(server.APIError):
                self.store.import_pack('Bad.zip', zipped(doc, files))
        self.assertEqual(self.store.list(), [])

    def test_archive_traversal_duplicate_paths_and_oversize_are_refused(self):
        doc, files = fixture()
        for name in ('../escape.txt', 'C:/escape.txt', 'Bear_team-bear/model.glb'):
            with self.assertRaisesRegex(server.APIError, 'unsafe or duplicate'):
                self.store.import_pack('Bad.zip', zipped(doc, files, (name, b'bad')))
        with patch.object(bear_pack, 'MAX_PACK', 32):
            with self.assertRaises(server.APIError):
                self.store.import_pack('Large.zip', zipped(doc, files))
        self.assertEqual(self.store.list(), [])

    def test_live_manifest_verifies_files_and_keeps_scanner_identity(self):
        doc, files = fixture()
        scanner = server.Scanner('http://127.0.0.1:8471')
        def get(path, limit=server.MAX_JSON):
            if path == '/api/v1/bears/team-bear':
                return json.dumps(doc).encode()
            name = path.split('/files/', 1)[1].split('?', 1)[0]
            return files[name]
        self.store.scanner = scanner
        with patch.object(scanner, 'get', get):
            bear = self.store.import_scanner('team-bear')['bear']
        self.assertEqual(bear['source']['kind'], 'scanner')
        self.assertEqual(bear['source']['pack']['revision'], doc['revision'])
        self.assertEqual(bear['source']['scannerUrl'], scanner.url)

    def test_live_pack_change_is_refused_without_legacy_fallback(self):
        doc, files = fixture()
        scanner = server.Scanner('http://127.0.0.1:8471')
        calls = []
        def get(path, limit=server.MAX_JSON):
            calls.append(path)
            if path == '/api/v1/bears/team-bear':
                value = copy.deepcopy(doc)
                if calls.count(path) > 1:
                    value['version'] += 1
                return json.dumps(value).encode()
            return files[path.split('/files/', 1)[1].split('?', 1)[0]]
        with patch.object(scanner, 'get', get):
            with self.assertRaisesRegex(server.APIError, 'changed during import'):
                scanner.source('team-bear')
        self.assertFalse(any(path.startswith('/api/scans') for path in calls))


if __name__ == '__main__':
    unittest.main()
