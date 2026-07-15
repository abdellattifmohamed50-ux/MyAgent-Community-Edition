#!/usr/bin/env sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
output_dir="$root_dir/release"
version=$(tr -d '[:space:]' < "$root_dir/VERSION")
base_name="MyAgent-Community-Edition-v${version}"
archive="$output_dir/${base_name}.zip"
checksum="$archive.sha256"

rm -rf "$output_dir"
mkdir -p "$output_dir"
cd "$root_dir"
python3 - "$archive" "$base_name" <<'PY'
import pathlib
import sys
import zipfile

root = pathlib.Path.cwd()
archive = pathlib.Path(sys.argv[1])
base_name = pathlib.Path(sys.argv[2])
excluded_names = {
    ".git", ".deps", ".deps-current", ".venv", "node_modules", "release",
    "release_evidence",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".coverage",
    ".DS_Store", "htmlcov", "build", "dist", "coverage.xml",
}
excluded_suffixes = {".pyc", ".db", ".sqlite3"}
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in excluded_names for part in relative.parts):
            continue
        if any(part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.suffix in excluded_suffixes:
            continue
        if path.name == ".env" or (
            path.name.startswith(".env.")
            and path.name not in {".env.example", ".env.production.example"}
        ):
            continue
        bundle.write(path, base_name / relative)
print(archive)
PY
python3 - "$archive" "$checksum" <<'PY'
import hashlib
import pathlib
import sys
archive = pathlib.Path(sys.argv[1])
checksum = pathlib.Path(sys.argv[2])
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
print(checksum)
PY
