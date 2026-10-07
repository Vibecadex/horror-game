# Bear Scanner integration in this fork

## Prerequisites

Use Windows, Python 3.11+, the installed Unreal Engine 5.8.3 and hydrated Git LFS game assets. `python tools/team_check.py` checks these without installing anything. Close Unreal before importing. Keep the saved chamber and its ownership separate from scan imports.

Use finished exports from [Vibecadex/bear-scanner](https://github.com/Vibecadex/bear-scanner), through its running workshop or a local GLB/folder. This fork contains a pinned editor importer under `tools/vendor`, with [source provenance](../tools/vendor/bear_scanner_importer.provenance.json). The wrapper records its exact SHA-256 in each receipt. Importing a local export needs no scanner checkout or running service. No packages are installed by this integration.

Set the dependency path and scanner address in the ignored `tools/project-settings.local.json`, preserving any engine override:

```json
{
  "bear_scanner_repo": "C:/Projects/to-deploy/bear-scanner",
  "bear_scanner_url": "http://127.0.0.1:8471"
}
```

These are this workstation's values. The default scanner address is `https://127.0.0.1:8443`. `bear_scanner_repo` locates the scanner's certificate (default `../bear-scanner/data/certs/cert.pem`); set it for a worktree using HTTPS, or supply an explicit `bear_cert`. Loopback HTTP and local exports need no certificate. No trust store is modified. Environment variables `BEAR_SCANNER_REPO`, `BEAR_SCANNER`, `BEAR_SOURCE`, and `BEAR_CERT` override local settings.

## Run

With the workshop running and at least one finished scan:

```powershell
.\IMPORT_BEARS.cmd
```

Or import a downloaded scanner export without a running service:

```powershell
.\IMPORT_BEARS.cmd "D:\Scans\Rupert.glb"
```

The argument can also be a scan folder. The launcher waits up to 30 minutes unless `TEDDY_TEST_TIMEOUT` is set. It uses the project's existing scoped Unreal runner and writes a new `evidence/implementation/<timestamp>-import_scanned_bears/` receipt and host exit result. A missing dependency, unavailable scanner, empty finished-scan list, or failed bear returns a failure.

Open this fork's `EDIT.cmd`, then find the result under `/Game/ScannedBears` in the Content Browser. Bears are static props; animation, rigging, boss replacement and level placement are separate work. The existing encounter is retained.

For the team's separate skeletal prototype, see the [native rigfit review](TEAM_RIG_NATIVE_REVIEW.md). Its synthetic fixture is saved under `/Game/ScannedBears/RigfitReview`, with a dedicated `REVIEW_TEAM_RIG.cmd`. This does not change the static import contract or automatically rig a scanned pack.

## Import behavior

The pinned importer now includes the team's bear-pack API 5 from scanner `8b396ab`: manifest-aware folders/ZIPs, versioned HTTP imports and model integrity metadata. It retains the local UE 5.8 reimport and authored-LOD corrections. Opaque IDs stay unchanged in metadata; Unreal names alone are sanitized. The latest sample and verification are described in [remote team continuation](REMOTE_TEAM_CONTINUATION.md).

- Each finished scan has one stable Static Mesh asset with its texture, convex collision, real centimetre dimensions and a base pivot. The scanner supplies three authored LODs.
- Unchanged scans are skipped. The upstream importer updates rebuilt or renamed scans at their existing mesh path.
- This fork saves staged materials/textures before moving them during reimport. A real forced update exposed UE 5.8's requirement that the source folder already exist on disk. The narrow correction is carried in the pinned importer; the live scanner checkout is unchanged.
- This fork disables Nanite on scanner-owned meshes. The first real editor check found it enabled by UE 5.8's defaults, producing a reduced fallback LOD0 and bypassing authored LOD switching. The wrapper repairs that setting once, validates decreasing nonempty LOD geometry, and avoids saving already-correct meshes on later runs.
- The team scanner's local uncommitted work is retained. The fork adds no native modules, installers, firewall changes or certificate trust changes.

## Verification and current limits

Run a fresh saved-asset check and three native LOD captures with:

```powershell
python tools/run_encounter_test.py tools/verify_scanned_bears.py
```

The check inspects saved ownership, scan identity/version, geometry counts, material/texture references, collision, pivot and Nanite state. It renders the first bear at 10x actor scale in an unsaved blank review world, forcing each LOD in turn. It does not save that world or alter the chamber.

The local finished scan is **Bundled real bear (prebuilt sample)**, scan ID `def16f899a9a`. Its live GLB is byte-identical to the team's bundled `web/examples/real-bear/model.glb`. It includes its supporting box and original scan-quality warnings. It was not reconstructed on this workstation.

The workshop currently reports its synthetic scan as failed. Its local setup notes identify Windows Application Control blocking an OpenMVS dependency. Importing finished scans is independent of that reconstruction blocker. Phone capture, new photo reconstruction, runtime loading in a packaged game and monster animation are not established by this editor integration.

Fresh integration evidence and preservation results are linked by [current-run.json](../evidence/bear-scanner/current-run.json). The original 786 tracked game Content/Config/project files are the preservation baseline; the unrelated untracked audio recording is excluded.

The [completed review](../evidence/bear-scanner/20261006T123838Z/QA_REVIEW.md) records 12/12 saved-asset checks, successful reimport, byte-identical unchanged repeats and three native LOD renders. [Preview the imported sample](../evidence/implementation/20261006T125809-verify_scanned_bears/bear-lod0.png).
