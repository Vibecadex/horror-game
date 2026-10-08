"""Open only the isolated chamber candidate, preserving the ordinary PLAY target."""
import argparse
import astra_setup as setup

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--edit', action='store_true')
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()
candidate = setup.ROOT / 'TeddyBlueprint/Content/Maps/TeddyChamberParity.umap'
setup.require_file(candidate)
# Process-local settings only; no settings file or global configuration is written.
setup.SETTINGS = dict(setup.SETTINGS, target_map='/Game/Maps/TeddyChamberParity')
raise SystemExit(setup.open_project('editor' if args.edit else 'play', dry_run=args.dry_run))
