"""components.toml: every component has a url and a ref, and fetch.py knows the keys used."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = {"url", "ref", "partial", "sparse"}


def test_every_component_has_a_url_and_a_ref():
    components = tomllib.loads((ROOT / "components.toml").read_text())
    assert components, "no components"
    for name, spec in components.items():
        assert spec.get("url") and spec.get("ref"), name
        assert set(spec) <= KEYS, f"{name}: unknown keys {set(spec) - KEYS}"
        assert isinstance(spec.get("sparse", []), list), name
