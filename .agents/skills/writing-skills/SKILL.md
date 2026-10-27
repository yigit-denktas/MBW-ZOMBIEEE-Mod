---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# Writing Skills

## Overview

**Writing skills IS Test-Driven Development applied to process documentation.**

**Personal skills live in your runtime's skills directory** (`~/.claude/skills/` on Claude Code) — see the upstream `using-superpowers` references for the path on other runtimes. Codex, Copilot CLI, and Gemini CLI also recognize `~/.agents/skills/` as a cross-runtime alias.

You write test cases (pressure scenarios with subagents), watch them fail (baseline behavior), write the skill (documentation), watch tests pass (agents comply), and refactor (close loopholes).

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

**REQUIRED BACKGROUND:** Understand superpowers:test-driven-development before using this skill. That skill defines the RED-GREEN-REFACTOR cycle. This skill adapts TDD to documentation.

## What is a Skill?

A **skill** is a reference guide for proven techniques, patterns, or tools. Skills help future agents find and apply effective approaches.

**Skills are:** Reusable techniques, patterns, tools, reference guides

**Skills are NOT:** Narratives about how you solved a problem once

## TDD Mapping for Skills

| TDD Concept | Skill Creation |
|-------------|----------------|
| **Test case** | Pressure scenario with subagent |
| **Production code** | Skill document (SKILL.md) |
| **Test fails (RED)** | Agent violates rule without skill (baseline) |
| **Test passes (GREEN)** | Agent complies with skill present |
| **Refactor** | Close loopholes while maintaining compliance |

The entire skill creation process follows RED-GREEN-REFACTOR.

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)
- Others would benefit

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (put in your instructions file)
- Mechanical constraints (if enforceable with regex/validation, automate it)

## Skill Types

### Technique
Concrete method with steps to follow (condition-based-waiting, root-cause-tracing)

### Pattern
Way of thinking about problems (flatten-with-flags, test-invariants)

### Reference
API docs, syntax guides, tool documentation

## Directory Structure

```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Only if needed
```

Flat namespace. Separate files only for heavy reference (100+ lines) or reusable tools. Keep principles and short code patterns inline.

## Writing SKILL.md

A skill's `description` says only when to use it: triggering conditions and symptoms, starting with "Use when...". It never summarizes the skill's workflow, because an agent that reads a workflow summary follows it instead of reading the skill.

YAML frontmatter requires `name` and `description`; name uses only letters, numbers, hyphens; description max 1024 chars, third person, starts with "Use when...".

## The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

This applies to NEW skills AND EDITS to existing skills.

Write skill before testing? Delete it. Start over. Edit skill without testing? Same violation.

**No exceptions:** not for simple additions, not for just adding a section, not for documentation updates, not for "I'll test later".

## Testing All Skill Types

### Discipline-Enforcing Skills (rules/requirements)
Test with academic questions, pressure scenarios, combined pressures. Success: agent follows rule under maximum pressure.

### Technique Skills (how-to)
Test application, variation, missing-information scenarios. Success: agent applies technique to new scenario.

### Pattern Skills (mental models)
Test recognition, application, counter-examples. Success: agent identifies when/how and when NOT.

### Reference Skills (docs/APIs)
Test retrieval, application, gap coverage. Success: agent finds and applies reference.

## Common Rationalizations for Skipping Testing

| Excuse | Reality |
|--------|---------|
| "Skill is obviously clear" | Clear to you ≠ clear to other agents. Test it. |
| "It's just a reference" | References can have gaps. Test retrieval. |
| "Testing is overkill" | Untested skills have issues. 15 min saves hours. |
| "I'll test if problems emerge" | Problems = agents can't use skill. Test before deploying. |
| "No time to test" | Deploying untested skill wastes more time later. |

## Match the Form to the Failure

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Skips/violates a rule under pressure | Prohibition + rationalization table + red flags | Soft guidance ("prefer", "consider") |
| Output has wrong shape | Positive recipe/contract: parts, in order | Prohibition list |
| Omits required element | Structural required field/slot | Prose reminder |
| Behavior depends on condition | Conditional keyed to observable predicate | Unconditional rule + exemptions |

Rules for whichever form: no nuance clauses; exemption clauses don't scope; restructure if output must be exempt.

## RED-GREEN-REFACTOR for Skills

### RED: Write Failing Test (Baseline)
Run pressure scenario WITHOUT the skill. Document exact behavior, rationalizations verbatim, triggering pressures.

### GREEN: Write Minimal Skill
Write skill addressing those specific rationalizations. Re-run scenarios WITH skill.

### REFACTOR: Close Loopholes
New rationalization? Add explicit counter. Re-test until bulletproof.

### Micro-Test Wording
One fresh-context sample per call; include a no-guidance control; 5+ reps per variant; manually read flagged matches; variance is a metric. Micro-tests verify wording, not discipline compliance.

## Anti-Patterns

- Narrative example: "In session..., we found..." — too specific, not reusable.
- Multi-language dilution.
- Code in flowcharts.
- Generic labels (helper1, step3).

## Deployment Checklist

- [ ] RED baseline documented
- [ ] Name/description valid
- [ ] Addresses specific baseline failures
- [ ] Form matches failure type
- [ ] One excellent example
- [ ] GREEN scenario passes
- [ ] Refactor loopholes closed
- [ ] Committed/deployed

## Discovery Workflow

Future agent encounters problem → searches skill descriptions → finds SKILL → scans overview → reads patterns → loads example only when implementing. Put searchable terms early and often.

## Upstream

Installed from `obra/superpowers` `skills/writing-skills` on 2026-10-24. Preserve this attribution when editing; local project skills should follow this process.
