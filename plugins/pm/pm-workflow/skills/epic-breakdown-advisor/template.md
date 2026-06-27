# Epic Breakdown Plan Template

Use this template to document an epic-to-story breakdown applying Richard Lawrence's 9 Humanizing Work splitting patterns. Output is a complete plan including pre-split validation, applied pattern, story breakdown (use case + Gherkin AC), split evaluation, and INVEST validation.

## Provenance
Adapted from `prompts/epic-breakdown-advisor.md` in the `https://github.com/deanpeters/product-manager-prompts` repo (Richard Lawrence & Peter Green, *The Humanizing Work Guide to Splitting User Stories*).

## Template
```markdown
# Epic Breakdown Plan

**Epic:** [Original epic title or one-line description]
**Pre-Split Validation:** ✅ Passes INVEST (except Small)
**Splitting Pattern Applied:** [Pattern 1-9 name, e.g., "Pattern 7: Simple/Complex"]
**Rationale:** [Why this pattern fits — what core complexity it isolates]

---

## Story Breakdown

### Story 1: [Title] (Simplest Complete Slice)

**Summary:** [User-value-focused title]

**Use Case:**
- **As a** [persona / role]
- **I want to** [action the user takes]
- **so that** [desired outcome for the user]

**Acceptance Criteria:**
- **Given:** [Initial context or precondition]
- **When:** [Event that triggers the action]
- **Then:** [Expected outcome aligned to "so that"]

**Why This First:** [Delivers core value; simpler variations follow]
**Estimated Effort:** [Days / story points]

---

### Story 2: [Title] (First Variation)

**Summary:** [User-value-focused title]

**Use Case:**
- **As a** [persona]
- **I want to** [action]
- **so that** [outcome]

**Acceptance Criteria:**
- **Given:** [Precondition]
- **When:** [Trigger]
- **Then:** [Outcome]

**Why This Next:** [What variation/sophistication this adds]
**Estimated Effort:** [Days / story points]

---

### Story 3: [Title] (Second Variation)

[Repeat the same structure...]

---

## Split Evaluation

✅ **Does this split reveal low-value work?**
- [Analysis: Which stories could be deprioritized or eliminated based on user research / business value?]

✅ **Does this split produce equally-sized stories?**
- [Analysis: Are stories roughly equal in effort? List sizes — e.g., Story 1 = 3 days, others = 1 day]

---

## INVEST Validation (Each Story)

✅ **Independent:** [Stories can be developed in any order; no blocking dependencies]
✅ **Negotiable:** [Implementation details can be discovered collaboratively]
✅ **Valuable:** [Each story delivers observable user value]
✅ **Estimable:** [Team can size each story relatively]
✅ **Small:** [Each story fits in 1-5 days]
✅ **Testable:** [Clear acceptance criteria for each story]

---

## Next Steps

1. **Review with team:** Do PM, design, engineering agree on the breakdown?
2. **Check for further splitting:** Are any stories still > 5 days? If yes, **restart at Pattern 1** for that story.
3. **Prioritize:** Which story delivers most value first?
4. **Consider eliminating:** Did the split reveal low-value stories? Kill or defer them.
```

## Notes

- **Pattern selection order**: Patterns must be tried in order 1→9; the first that fits wins. Do not jump to a later pattern if an earlier one applies.
- **Vertical slicing required**: Each story must touch all architectural layers and deliver observable user value — never split into "front-end story" + "back-end story" (horizontal slicing is the #1 anti-pattern).
- **Re-split large stories**: If any story remains > 5 days after the first pass, **restart at Pattern 1** for that specific story; iterative splitting is normal (see Example 4 in `examples/sample.md`).
- **Spike is not a story**: Pattern 9 (spike) produces *learning*, not shippable code. After the spike, restart at Pattern 1 with reduced uncertainty.
- **Skip "Small" in INVEST check**: Pre-split validation deliberately excludes "Small" — that's why we're splitting in the first place. All other 5 INVEST criteria must pass before splitting.
