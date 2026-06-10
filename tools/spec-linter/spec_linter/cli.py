"""CLI: `python -m spec_linter.cli [path] [--emit-schema OUT.json]`.

Lints a spec file or a directory of specs; exits 1 if any verdict is FAIL,
else 0. The CLI is a consumer of the engine and owns the usage policy: YAML
loading, directory iteration, the cross-file duplicate-id (L4) check, and the
choice of the agent-spec contract for every linted file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from . import rules
from .contracts.agent_spec import AgentSpecContract, emit_json_schema
from .engine import lint
from .verdict import Level, Verdict

_CONTRACT = AgentSpecContract()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a YAML mapping at the top level")
    return data


def _lint_file(path: Path) -> Verdict:
    """Lint one YAML spec file against the agent-spec contract."""
    return lint(_load_yaml(path), _CONTRACT)


def _lint_dir(path: Path) -> dict[str, Verdict]:
    """Lint every `.yaml`/`.yml` file in a directory, keyed by file name.

    Adds the cross-file duplicate-id (L4) check on top of the per-file
    verdicts: a duplicated id appends the same finding to every file that
    claims it.
    """
    files = sorted(p for p in path.iterdir() if p.suffix in (".yaml", ".yml"))
    verdicts: dict[str, Verdict] = {}
    ids_by_source: dict[str, list[str]] = {}
    for file in files:
        data = _load_yaml(file)
        verdicts[file.name] = lint(data, _CONTRACT)
        spec_id = data.get("id")
        if isinstance(spec_id, str):
            ids_by_source.setdefault(spec_id, []).append(file.name)
    for spec_id, sources in ids_by_source.items():
        for finding in rules.l4_identity_findings({spec_id: sources}):
            for source in sources:
                verdicts[source] = Verdict.from_findings([*verdicts[source].findings, finding])
    return verdicts


def _write_schema(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(emit_json_schema(), indent=2) + "\n")
    print(f"Wrote JSON Schema to {out}")


def _lint_path(path: Path) -> Level:
    if path.is_dir():
        verdicts = _lint_dir(path)
        worst = Level.PASS
        for name, verdict in verdicts.items():
            print(f"== {name} ==")
            print(verdict)
            print()
            worst = max(worst, verdict.level)
        print(f"OVERALL: {worst.name}")
        return worst

    verdict = _lint_file(path)
    print(f"== {path.name} ==")
    print(verdict)
    return verdict.level


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spec_linter", description="AgentSpec contract-validation engine (the Linter)."
    )
    parser.add_argument("path", nargs="?", help="spec file or directory to lint")
    parser.add_argument(
        "--emit-schema",
        metavar="OUT.json",
        type=Path,
        help="write the spec JSON Schema to OUT.json",
    )
    args = parser.parse_args(argv)

    if args.emit_schema is not None:
        _write_schema(args.emit_schema)
        if args.path is None:
            return 0

    if args.path is None:
        parser.error("a path is required unless only --emit-schema is given")

    level = _lint_path(Path(args.path))
    return 1 if level == Level.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
