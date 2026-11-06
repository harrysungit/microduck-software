#!/usr/bin/env python3
"""Fetch the repositories listed in components.toml into components/<name>/.

    python3 scripts/fetch.py                      # every component at its ref
    python3 scripts/fetch.py studio rl            # only these
    python3 scripts/fetch.py --release releases/<file>.toml

A component already fetched is updated in place: fetched again and checked out at its
ref (or at the release's commit), detached. Local changes in a component stop the
fetch rather than being overwritten.

MICRODUCK_COMPONENT_<NAME>=<path or url> replaces a component's url, e.g. a local
checkout that is not published yet (MICRODUCK_COMPONENT_RL=~/src/microduck-rl).
"""

import argparse
import os
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args, cwd=None, capture=False):
    result = subprocess.run(["git", *args], cwd=cwd, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else ""


def fetch(name: str, spec: dict, commit: str | None) -> str:
    dest = ROOT / "components" / name
    url = os.path.expanduser(os.environ.get(f"MICRODUCK_COMPONENT_{name.upper()}", spec["url"]))
    ref = commit or spec["ref"]
    if not (dest / ".git").exists():
        args = ["clone", "--quiet", "--no-checkout"]
        if spec.get("partial") and "://" in url:
            args.append("--filter=blob:none")
        git(*args, url, str(dest))
        if spec.get("sparse"):
            git("sparse-checkout", "set", "--cone", *spec["sparse"], cwd=dest)
    else:
        if git("status", "--porcelain", cwd=dest, capture=True):
            sys.exit(f"{name}: local changes in {dest}; commit or move them first")
        git("remote", "set-url", "origin", url, cwd=dest)
        git("fetch", "--quiet", "origin", cwd=dest)
    target = ref if commit else (f"origin/{ref}" if git("ls-remote", "--heads", "origin", ref, cwd=dest, capture=True)
                                 else ref)
    git("checkout", "--quiet", "--detach", target, cwd=dest)
    return git("rev-parse", "HEAD", cwd=dest, capture=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="components to fetch; default: all")
    ap.add_argument("--release", type=Path, help="a release file from releases/: check out its commits")
    args = ap.parse_args()

    components = tomllib.loads((ROOT / "components.toml").read_text())
    commits = {}
    if args.release:
        commits = {k: v["commit"] for k, v in tomllib.loads(args.release.read_text())["components"].items()}
    names = args.names or list(components)
    unknown = [n for n in names if n not in components]
    if unknown:
        sys.exit(f"unknown component(s): {', '.join(unknown)}; see components.toml")
    for name in names:
        head = fetch(name, components[name], commits.get(name))
        print(f"{name:8s} {head[:12]}  components/{name}")


if __name__ == "__main__":
    main()
