#!/usr/bin/env python3
"""
Assert that the agent-context docs still match the code they describe.

Direction matters: the SOURCE is the truth, the DOCS are under test. Every check
below extracts a fact from the codebase and asserts the docs state it correctly.
This is deliberately NOT a snapshot/golden test - it must not fire when someone
legitimately edits prose, only when a doc and its source disagree.

Why this exists: an audit in Aug 2026 found five factual errors that had
accumulated in the agent context unnoticed - including "return_to_origin is a
Mission subclass" (it is a plain rclcpp::Node) and a clang-format rule stated
exactly backwards. Agents and new members consume these files as fact, so a wrong
line here sends someone down the wrong path with no feedback. Each check is cheap
to write once the claim is known; the reason drift happened is that nobody wrote
the assertion, not that detecting it was hard.

MAINTAINING THIS FILE
  - Assert LOAD-BEARING facts only: the ones that would send someone down the
    wrong path. Not every sentence. The cost of each check lands on whoever edits
    these docs next, so keep the list short and high-value.
  - A check that fails for a legitimate doc edit is a bug in the check. Fix or
    delete it - do not train people to ignore red.
  - Deleting a check is a normal, expected edit. If a fact stops being
    load-bearing, remove its assertion rather than maintaining it forever.
  - Add one when review catches a doc error: that is proof the fact is
    load-bearing and that humans miss it.
  - Deliberate exceptions go in ALLOWED_MISSING_PATHS with a reason, not by
    weakening a check.

Usage:  python3 scripts/check-docs.py [--quiet]
Exit:   0 = docs agree with source, 1 = at least one disagreement
Deps:   python3 stdlib only. No network, no API key, runs in ~1s.
"""

import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Docs under test. Adding a context doc? Add it here.
DOC_PATHS = ["AGENTS.md", "CLAUDE.md"] + sorted(
    str(p.relative_to(ROOT)) for p in (ROOT / "docs/context").glob("*.md")
)

# Paths the docs mention that intentionally do not exist. Each needs a reason:
# without this, a doc that correctly documents a broken path gets flagged.
ALLOWED_MISSING_PATHS = {
    "gz_worlds/aeac": "simulateTask2.sh points here, but the file is aeac.sdf - "
                      "the docs cite the broken path while explaining the bug",
}

results = []  # (ok: bool, check: str, detail: str)


def assert_(check, ok, detail=""):
    results.append((bool(ok), check, detail))


def source(rel):
    """Read a source file. Missing file is itself a failure, not a crash."""
    p = ROOT / rel
    if not p.exists():
        assert_("source file present", False, f"expected to find {rel}")
        return ""
    return p.read_text(encoding="utf-8")


DOCS = {p: (ROOT / p).read_text(encoding="utf-8") for p in DOC_PATHS if (ROOT / p).exists()}
BLOB = "\n".join(DOCS.values())


# --------------------------------------------------------------------------
# Mission FSM - source of truth: mission_core/include/mission_core/mission.hpp
# --------------------------------------------------------------------------
MISSION_HPP = "ros_ws/src/flight_missions/mission_core/include/mission_core/mission.hpp"
hpp = source(MISSION_HPP)

m = re.search(r"enum\s+FSM\s*:\s*\w+\s*\{([^}]*)\}", hpp, re.S)
if m:
    states = [s.strip() for s in m.group(1).split(",")
              if s.strip() and not s.strip().startswith("//")]
    assert_("FSM enum parsed", len(states) >= 2, f"only found {states}")

    # Every real state is documented...
    for st in states:
        assert_("FSM state documented", f"`{st}`" in BLOB,
                f"`{st}` is in enum FSM ({MISSION_HPP}) but appears in no context doc")

    # ...and no doc invents one that no longer exists. Catches renames, which a
    # one-directional check would miss entirely.
    for cited in set(re.findall(r"`([A-Z][A-Za-z]{4,})`", BLOB)):
        looks_like_state = cited in {
            "Init", "OffboardRequested", "WaitForStableOffboard", "ArmRequested",
            "MissionObjective", "FinishPolicyRequested", "FinishPolicyMonitor",
            "Finished", "Failed", "Approach", "ManualRequested",
        }
        if looks_like_state:
            assert_("FSM state still exists", cited in states,
                    f"docs cite FSM state `{cited}`, which is not in enum FSM - renamed or removed?")
else:
    assert_("FSM enum found", False, f"could not parse `enum FSM` from {MISSION_HPP}")

# Pure virtuals are the REQUIRED overrides. Documenting these wrong is the exact
# error the Aug 2026 audit found, so both directions are checked.
pure_virtuals = set(re.findall(r"virtual\s+[\w:<>]+\s+(\w+)\s*\([^)]*\)\s*=\s*0", hpp))
assert_("pure virtuals parsed", len(pure_virtuals) >= 1, "found none - did the header change shape?")
for fn in pure_virtuals:
    assert_("required override documented", f"`{fn}()`" in BLOB,
            f"{fn}() is pure virtual (a REQUIRED override) but no context doc mentions it")

# FinishPolicy values
m = re.search(r"enum\s+FinishPolicy\s*:\s*\w+\s*\{([^}]*)\}", hpp, re.S)
if m:
    for pol in [s.strip() for s in m.group(1).split(",") if s.strip()]:
        assert_("FinishPolicy documented", f"`{pol}`" in BLOB,
                f"FinishPolicy::{pol} is undocumented")


# --------------------------------------------------------------------------
# Which mission_nodes actually subclass Mission
# This is the check that would have caught the return_to_origin error.
# --------------------------------------------------------------------------
NODES_DIR = ROOT / "ros_ws/src/flight_missions/mission_nodes"
cmake = source("ros_ws/src/flight_missions/mission_nodes/CMakeLists.txt")
declared = set(re.findall(r"add_executable\(\s*(\w+)", cmake))

subclasses = set()
if NODES_DIR.exists():
    for f in list(NODES_DIR.rglob("*.hpp")) + list(NODES_DIR.rglob("*.cpp")):
        if re.search(r":\s*public\s+Mission\b", f.read_text(encoding="utf-8")):
            subclasses.add(f.stem)

for exe in sorted(declared - subclasses):
    # Not an error in itself - but the docs must not call it a Mission.
    claims_mission = re.search(
        rf"`{re.escape(exe)}`[^.\n]{{0,120}}(built on|subclass(es)?|concrete mission)s?\s+`?Mission`?",
        BLOB)
    assert_("non-Mission node not mislabelled", not claims_mission,
            f"`{exe}` does NOT inherit Mission (no ': public Mission' in its sources), "
            f"but a context doc describes it as one")


# --------------------------------------------------------------------------
# ROS packages - source of truth: the ros_ws/src directory itself
# --------------------------------------------------------------------------
src_dir = ROOT / "ros_ws/src"
if src_dir.exists():
    for pkg in sorted(p.name for p in src_dir.iterdir() if p.is_dir()):
        assert_("package documented", f"`{pkg}`" in BLOB,
                f"package `{pkg}` exists in ros_ws/src but no context doc mentions it")


# --------------------------------------------------------------------------
# clang-format - stating these backwards actively misleads. Assert verbatim.
# --------------------------------------------------------------------------
cf = source(".clang-format")
for key in ("BreakBeforeBraces", "SpaceBeforeParens", "SpacesInParentheses", "AccessModifierOffset"):
    m = re.search(rf"^{key}:\s*(\S+)", cf, re.M)
    if m:
        assert_("clang-format rule stated verbatim", f"`{key}: {m.group(1)}`" in BLOB,
                f".clang-format has `{key}: {m.group(1)}`; no context doc states that verbatim")


# --------------------------------------------------------------------------
# DBSCAN parameters - three different values; quoting one as "the" value misleads
# --------------------------------------------------------------------------
cp = source("perception/circle_processing.py")
for var in ("min_samples_pt", "min_samples_pl", "eps_pt"):
    m = re.search(rf"^{var}\s*=\s*([\d.]+)", cp, re.M)
    if m:
        assert_("DBSCAN parameter documented", m.group(1) in BLOB,
                f"{var} = {m.group(1)} in circle_processing.py, but that value appears in no doc")


# --------------------------------------------------------------------------
# tmux pane count in the sim harnesses
# --------------------------------------------------------------------------
for script in ("scripts/simulateDepth.sh", "scripts/simulateTask2.sh"):
    body = source(script)
    if body:
        panes = 1 + len(re.findall(r"tmux split-window", body))
        # Accept a digit or the number written out ("five panes"), bolded or not.
        word = {4: "four", 5: "five", 6: "six", 7: "seven"}.get(panes, "")
        stated = any(f"{form} panes" in BLOB
                     for form in (str(panes), word, f"**{word}**") if form)
        assert_("tmux pane count documented", stated,
                f"{script} creates {panes} panes; no context doc states that number")


# --------------------------------------------------------------------------
# Every repo path the docs reference must exist
# --------------------------------------------------------------------------
PATH_RE = r"`((?:scripts|ros_ws|perception|deployment|gz_worlds|docs|\.devcontainer|\.github)/[\w./\-]+)`"
for path in sorted(set(re.findall(PATH_RE, BLOB))):
    if path in ALLOWED_MISSING_PATHS:
        continue
    assert_("referenced path exists", (ROOT / path).exists(),
            f"docs reference `{path}`, which does not exist "
            f"(if deliberate, add it to ALLOWED_MISSING_PATHS with a reason)")

# Every relative markdown link resolves
for doc, text in DOCS.items():
    base = (ROOT / doc).parent
    for link in re.findall(r"\]\((\.{0,2}[\w./\-]+\.md)\)", text):
        assert_("markdown link resolves", (base / link).exists(),
                f"{doc} links to `{link}`, which does not resolve")

# Stale allowlist entries are themselves drift
for path, reason in ALLOWED_MISSING_PATHS.items():
    assert_("allowlist entry still needed", not (ROOT / path).exists(),
            f"`{path}` is in ALLOWED_MISSING_PATHS but now exists - remove the entry ({reason})")


# --------------------------------------------------------------------------
# CLAUDE.md must import AGENTS.md, or Claude Code loses all project context
# --------------------------------------------------------------------------
if "CLAUDE.md" in DOCS:
    assert_("CLAUDE.md imports AGENTS.md",
            re.search(r"^@AGENTS\.md\s*$", DOCS["CLAUDE.md"], re.M) is not None,
            "CLAUDE.md must contain a bare `@AGENTS.md` import line. Claude Code does not "
            "auto-load AGENTS.md; a plain markdown link silently drops all project context.")


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
def main():
    quiet = "--quiet" in sys.argv
    failures = [(c, d) for ok, c, d in results if not ok]
    total = len(results)

    if failures:
        print(f"check-docs: {total - len(failures)}/{total} assertions passed, "
              f"{len(failures)} FAILED\n")
        for check, detail in failures:
            print(f"  FAIL  [{check}]")
            print(f"        {detail}\n")
        print("The agent-context docs disagree with the code they describe.")
        print("Fix the doc, or if the doc is right and this check is wrong, fix")
        print("scripts/check-docs.py - see the maintenance notes at the top.")
        return 1

    if not quiet:
        print(f"check-docs: {total}/{total} assertions passed - "
              f"agent context agrees with source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
