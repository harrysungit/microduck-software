"""tools/hd1910_protection.py against Microduck Studio's protocol-level simulated bus (sim_bus.SimSerial).

Skipped until `python3 scripts/fetch.py` has fetched the Studio component, which brings feetech.py
and sim_bus.py.
"""
import contextlib
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "components/studio/software/studio"))
sys.path.insert(0, str(ROOT / "tools"))
pytest.importorskip("serial")
feetech = pytest.importorskip("studio.bus.feetech", reason="run scripts/fetch.py to fetch the Studio component")
sim_bus = pytest.importorskip("studio.bus.sim_bus", reason="run scripts/fetch.py to fetch the Studio component")
import hd1910_protection as hp  # noqa: E402

ALL = [10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 30, 31, 32, 33, 34]


def make_bus(present):
    ser = sim_bus.SimSerial(present)
    for s in ser.servos.values():
        s.r[19] = 4          # the factory value fanhao375/microduck-replica reports: overheat only
        s.r[14] = 100        # 10.0 V
    ser.servos[11].r[19] = 13            # already complete
    ser.servos[12].r[19] = 2             # encoder only: 15 once completed
    return ser, feetech.FeetechBus(None, ser=ser)


def run(argv, bus):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = hp.main(argv, bus=bus)
    return rc, out.getvalue()


def test_check_only_writes_nothing():
    ser, bus = make_bus([i for i in ALL if i != 33])
    # Registers 0-55 only (version, EEPROM, SRAM control): from 56 on the simulator refreshes feedback on every read.
    before = {i: bytes(s.r[:56]) for i, s in ser.servos.items()}
    rc, out = run([], bus)
    assert rc == 1, out
    assert "#33  no answer" in out, out
    assert "off: voltage, over-current" in out, out
    for i, s in ser.servos.items():
        assert bytes(s.r[:56]) == before[i], f"#{i}: a writable register changed in read-only mode"


def test_apply_sets_bits_keeps_others_and_relocks():
    ser, bus = make_bus(ALL)
    rc, out = run(["--apply"], bus)
    assert rc == 0, out
    for i, s in ser.servos.items():
        want = 15 if i == 12 else 13
        assert s.r[19] == want, f"#{i} 19 = {s.r[19]}, expected {want}"
        assert s.r[55] == 1, f"#{i} not relocked"
        assert s.r[20] == 0, f"#{i} register 20 changed without --led"
    assert "write 19: 13" not in out, "#11 is already complete and must not be written"


def test_apply_led_and_rerun_is_clean():
    ser, bus = make_bus(ALL)
    rc, _ = run(["--apply", "--led"], bus)
    assert rc == 0
    assert all(s.r[20] == 13 for s in ser.servos.values())
    rc, out = run([], bus)
    assert rc == 0, out
    assert "All three protections are on" in out, out


def test_led_without_apply_is_rejected():
    _, bus = make_bus(ALL)
    with pytest.raises(SystemExit) as e, contextlib.redirect_stderr(io.StringIO()):
        hp.main(["--led"], bus=bus)
    assert e.value.code == 2
