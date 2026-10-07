"""Pack identity regressions in the pinned importer; no Unreal process required."""
import ast
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(__file__).parent / 'vendor/bear_scanner_importer.py'


def importer_functions():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    wanted = {'safe', 'source_identity', 'pack_bear', 'sync', 'find_existing'}
    nodes = [node for node in tree.body if
             (isinstance(node, ast.FunctionDef) and node.name in wanted) or
             (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('PACK_FORMAT', 'PLAIN_NAME') for t in node.targets))]
    env = {'re': re, 'json': json, 'hashlib': hashlib, 'Path': Path}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), env)
    return env


class PackIdentity(unittest.TestCase):
    def test_pack_identity_is_preserved_and_aliases_stay_distinct(self):
        env = importer_functions()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            model = b'identity parser fixture'
            (root / 'model.glb').write_bytes(model)
            ids = ['example-real-bear', 'example_real_bear', 'a' * 24 + 'left', 'a' * 24 + 'right']
            results = []
            for identity in ids:
                manifest = {'format': 'bear-pack', 'formatVersion': 1, 'id': identity, 'name': 'Bear', 'version': 10,
                            'model': {'file': 'model.glb'}, 'files': {'model.glb': {'sha256': hashlib.sha256(model).hexdigest()}}}
                (root / 'manifest.json').write_text(json.dumps(manifest))
                results.append(env['pack_bear'](root)['id'])
            self.assertEqual(results, ids)
            self.assertEqual(len(set(results)), 4)

    def test_same_package_name_cannot_replace_a_different_bear(self):
        env = importer_functions()
        env.update(DEST='/Game/ScannedBears/ContractTest', SCAN_TAG='BearScanId', find_existing=lambda _: None,
                   asset_class=lambda _: 'StaticMesh', assets=SimpleNamespace(
                       does_directory_exist=lambda _: True, list_assets=lambda *a, **k: ['/Game/ScannedBears/ContractTest/Bear_same/SM_Bear'],
                       load_asset=lambda _: object(), get_metadata_tag=lambda *a: 'another-bear'))
        with self.assertRaisesRegex(RuntimeError, 'different bear identity'):
            env['sync']({'id': 'incoming-bear', 'name': 'Bear', 'key': 'Bear_same'})

    def test_matching_identity_does_not_grant_ownership(self):
        env = importer_functions()
        env.update(DEST='/Game/ScannedBears', SCAN_TAG='BearScanId', OWNER_TAG='BearScanner.Owner', OWNER='bear-scanner',
                   asset_class=lambda _: 'StaticMesh', assets=SimpleNamespace(
                       does_directory_exist=lambda _: True, list_assets=lambda *a, **k: ['/Game/ScannedBears/Bear/SM_Bear'],
                       load_asset=lambda _: object(), get_metadata_tag=lambda _, tag: 'same-id' if tag == 'BearScanId' else 'someone-else'))
        with self.assertRaisesRegex(RuntimeError, 'unowned mesh'):
            env['find_existing']('same-id')


if __name__ == '__main__':
    unittest.main(verbosity=2)
