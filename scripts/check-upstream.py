#!/usr/bin/env python3
"""Ensure vendored schemas, corpus, and grader are byte-identical to the pinned checkout."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkout", type=Path)
    arguments = parser.parse_args()
    upstream = arguments.checkout.resolve()
    pin = json.loads((ROOT / "upstream.json").read_text())
    actual = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
    if actual != pin["commit"]:
        raise SystemExit(f"upstream checkout is {actual}, expected {pin['commit']}")
    mappings = [(upstream / "schemas/littlehorse", ROOT / "schemas"), (upstream / "sdk-conformance/areas", ROOT / "conformance/areas")]
    for source, destination in mappings:
        expected = {path.relative_to(source) for path in source.rglob("*") if path.is_file() and path.suffix.lower() not in {".md", ".markdown"}}
        present = {path.relative_to(destination) for path in destination.rglob("*") if path.is_file() and path.suffix.lower() not in {".md", ".markdown"}}
        if expected != present:
            raise SystemExit(f"file set differs in {destination}: {expected ^ present}")
        for relative in expected:
            if (source / relative).read_bytes() != (destination / relative).read_bytes():
                raise SystemExit(f"vendored file differs: {destination / relative}")
    for name in ["run.mjs", "lib.mjs", "compare.mjs", "fuzz.mjs"]:
        if (upstream / "sdk-conformance/runner" / name).read_bytes() != (ROOT / "conformance" / name).read_bytes():
            raise SystemExit(f"vendored grader differs: {name}")
    print(f"Schemas, corpus, and grader match upstream {actual}")


if __name__ == "__main__":
    main()
