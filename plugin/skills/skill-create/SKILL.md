---
name: skill-create
description: |
  SOP for creating a well-formed Claude Code skill in the current repository — naming,
  single-responsibility scoping, SKILL.md structure, YAML frontmatter hygiene, validation,
  and description optimization. Use when the user wants to create a new skill, turn a
  recurring workflow into a skill, or asks how to structure, name, validate, or describe
  a skill — e.g. "create a skill for X", "make this a skill", "encode this process as a
  skill". Do not use for creating agents or knowledge bases — those have their own workflows.
---

# Skill Create

Create a Claude Code skill that is correctly named, correctly scoped, and reliably triggered.
A good skill serves two purposes at once: direct value, because it automates an operation, and
executable documentation, because the body is the written business rule of that workflow —
readable as an SOP even by someone who never runs it.

## When to use

- The user wants to encode a recurring workflow or process as a skill.
- The user asks to create, structure, name, validate, or debug a skill.
- A prompt has been repeated (and corrected) across enough sessions that its steps are stable.

## Skip if

- The workflow still changes every run — run it as a plain prompt a few more times, because a
  skill freezes a procedure and freezing a moving target creates rework.
- The user wants an agent (an autonomous role with its own tools) or a knowledge base — those
  are different artifact types with their own creation workflows.
- The task is one-off — a skill only pays for itself through repetition.

## Principles

- **Single responsibility.** One skill equals one capability. When a skill accumulates
  unrelated triggers or produces two unrelated outputs, split it — two focused skills trigger
  more reliably than one blurry one.
- **The description triggers; the body instructs.** The description exists only to make the
  model open the skill at the right moment. Business rules — steps, constraints, output shape,
  the reasoning behind each rule — live in the body, because the body is what is read at run
  time.
- **Progressive disclosure.** Keep SKILL.md lean and push bulk into supporting files loaded on
  demand, because everything in SKILL.md costs context on every invocation.
- **Explain the why.** Give each rule its reason in one clause; a rule with a reason survives
  future edits, while a bare imperative invites deletion.

## Naming

- Use kebab-case: lowercase letters, digits, and hyphens matching
  `^[a-z0-9]+(-[a-z0-9]+)+$`, at most 64 characters.
- Make the `name` field equal the folder name — discovery and invocation key on the folder, so
  a mismatch makes the skill hard to find and confusing to call.
- Prefer domain-verb or domain-noun compounds — `kb-build`, `github-post-issue`,
  `changelog-update` — because the compound tells a reader both the domain and the action.
- Require at least one hyphen (the regex above enforces it) — single-word names collide with
  other tools and read as ambiguous.
- Avoid noise words: `helper`, `tool`, `utils`, and a `-skill` suffix add zero information,
  since everything in the skills folder is already a skill.
- Avoid bare `-er` agent-style names for skills (`code-reviewer`, `issue-poster`) — they read
  as an agent role rather than a procedure. Name the action instead: `code-review`,
  `github-post-issue`.

## Frontmatter hygiene

The frontmatter is YAML, and YAML plain scalars fail in ways that are easy to miss:

- A ` #` (space plus hash) inside an unquoted description starts a YAML comment and silently
  truncates the value:

  ```yaml
  # Broken — parses without error, but the value ends before the hash:
  description: Posts a weekly summary to the #data channel
  # The model receives only: "Posts a weekly summary to the"
  ```

- A `: ` (colon plus space) inside an unquoted value breaks parsing outright:

  ```yaml
  # Broken — YAML reads a nested mapping and fails to load:
  description: Reminder: run this before every release
  ```

- Use a literal block (`|`) for any multi-line description — it sidesteps both gotchas and
  keeps long descriptions readable:

  ```yaml
  # Correct:
  description: |
    Posts a weekly summary to the #data channel.
    Use when the user asks for the weekly channel summary.
  ```

- Do not invent frontmatter keys. There is no `triggers:` field — the `description` is the
  trigger mechanism, and unknown keys are ignored at best or break loading at worst.
- Keep only supported keys: `name`, `description`, and optionally `license`, `allowed-tools`,
  `metadata`, `compatibility`.

### Writing the description

The description is the single lever that decides when the skill fires, so write it
deliberately:

- Write in third person, capability first — state what the skill does before anything else.
- Follow with concrete trigger phrases users would actually say ("create a skill for X",
  "make this a skill") — matching happens against user wording, so use their words, not yours.
- End with an explicit negative boundary — "Do not use for X — use Y instead" — to prevent
  over-triggering on neighboring tasks.
- Stay at or under 1024 characters.
- Err slightly pushy: skills are under-triggered far more often than over-triggered, so a
  description that leans forward beats one that hedges.
- Test with near-miss queries that should NOT trigger ("create an agent", "write a README")
  and confirm the skill stays silent.

## Structure and progressive disclosure

Keep SKILL.md under ~500 lines. Push detail into three supporting folders, each with its own
loading semantics:

- `references/` — long-form documentation the model reads on demand (format specs, style
  guides, decision tables).
- `scripts/` — deterministic helpers the model runs instead of reimplementing (validators,
  renderers), because a script gives the same answer every time.
- `assets/` — files used in the output itself (templates, boilerplate the skill fills in).

Reference every supporting file from the body and state when to read or run it — the model
only loads what the body points to, so an unreferenced file is dead weight.

Example layout:

```
csv-validate/
├── SKILL.md                # always loaded when the skill runs — keep it lean
├── references/
│   └── schema-spec.md      # read before judging any file
├── scripts/
│   └── validate.py         # run on the target file; do not reimplement it
└── assets/
    └── report-template.md  # fill in and emit as the output
```

Minimal SKILL.md skeleton:

```markdown
---
name: csv-validate
description: |
  Validates CSV files against a column schema and reports violations.
  Use when the user wants to validate, check, or lint a CSV file, or
  asks why a CSV import fails. Do not use for Excel files.
---

# CSV Validate

Validate a CSV file against the column schema and report every violation.

## Process

1. Read references/schema-spec.md for the column rules (before judging any file).
2. Run scripts/validate.py on the target file (deterministic — do not eyeball it).
3. Fill assets/report-template.md with the violations, grouped by column.
```

If any asset is a template with `{{PLACEHOLDER}}` tokens, treat an unfilled token as a
failure: after every scaffold or render step, `grep -E '\{\{[A-Z_]+\}\}'` over the output
must return nothing.

## Process

1. **Capture the workflow.** Pin down four things with the user: what the skill does, when it
   should trigger, what it outputs, and where the output persists. If any of the four is
   fuzzy, the workflow has not settled — keep running it manually.
2. **Scope it.** Apply single responsibility. If the capture yields two outputs with unrelated
   triggers, split into two skills now — splitting later means rewriting two descriptions and
   retraining users.
3. **Name it** per the Naming rules, and create the folder with exactly that name.
4. **Write SKILL.md.** Frontmatter per the hygiene rules; body as an imperative SOP that
   explains the why of each step; bulk pushed to `references/`, `scripts/`, and `assets/`,
   each referenced with its read-or-run condition.
5. **Validate** against the checklist below. If the repository packages skills into a plugin,
   also run the plugin's build or validate command (for example `claude plugin validate`) and
   confirm the new skill appears in the listing.
6. **Optimize the description** once the skill has settled — not on a moving draft, because
   the tuning cost is one-time and amortizes over every future trigger. Probe with real
   trigger phrases and with near-miss queries; tighten until both behave.
7. **Iterate after real use.** Fold in every correction the user had to make. The skill is
   done when a fresh session runs it end-to-end without correction.

## Validation checklist

| Check | How | Pass condition |
|---|---|---|
| Frontmatter parses | load the YAML block with any parser | loads clean; `name` and `description` non-empty |
| Name well-formed | match `^[a-z0-9]+(-[a-z0-9]+)+$`, length at most 64 | matches, and equals the folder name |
| Description length | count characters of the description value | at most 1024 |
| Body size | `wc -l SKILL.md` | under ~500 lines |
| Supporting files exist | resolve every `references/`, `scripts/`, `assets/` path named in the body | every file exists on disk |
| Plugin build (if packaged) | run the plugin's validate or build command | skill appears in the listing with no errors |
| No leftover placeholders | `grep -E '\{\{[A-Z_]+\}\}'` on rendered output | zero matches |

Fix every failing row and re-run the whole checklist until it is clean — partial validation
gives false confidence.
