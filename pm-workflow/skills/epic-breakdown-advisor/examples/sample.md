# Epic Breakdown Example

## Example: Iterative Splitting of a Checkout Epic (Multiple Patterns Applied)

This example shows how a single large epic typically requires **multiple splitting passes** through the 9 Humanizing Work patterns until every resulting story fits in 1-5 days. Pattern selection cascades: Pattern 1 (Workflow) is tried first; surviving large stories are re-split with subsequent patterns.

```markdown
# Epic Breakdown Plan

**Epic:** Checkout flow with discounts (member, VIP, first-time) and payment (Visa, Mastercard, Amex)
**Pre-Split Validation:** ✅ Passes INVEST (except Small)
**Splitting Pattern Applied:** Multi-pass — Pattern 1 (Workflow) → Pattern 3 (Business Rules) → Pattern 6 (Major Effort)
**Rationale:** Single epic spans a multi-step workflow (cart → discount → payment), each step containing further variation (rule variations for discounts, infrastructure-heavy first-time effort for payment). Iterative re-splitting is required.

---

## Story Breakdown

### Story 1: Add items to cart (Simplest Complete Slice)

**Summary:** User can build a cart from product list.

**Use Case:**
- **As a** registered shopper
- **I want to** add products to my cart from the product list page
- **so that** I can review and proceed to discount/payment in subsequent steps

**Acceptance Criteria:**
- **Given:** I am viewing the product list with items in stock
- **When:** I click "Add to Cart" on any product
- **Then:** The item appears in my cart with correct quantity, and the cart icon shows the updated count

**Why This First:** Cart construction is the prerequisite — discount and payment have no meaning without items selected.
**Estimated Effort:** 2 days

---

### Story 2a: Apply member discount (10%) — First Business Rule Variation

**Summary:** Members receive 10% off cart subtotal.

**Use Case:**
- **As a** member-tier shopper
- **I want to** see my 10% member discount automatically applied at checkout
- **so that** I receive my membership benefit without manually entering codes

**Acceptance Criteria:**
- **Given:** I am logged in as a member-tier shopper with items in cart
- **When:** I navigate to the discount step of checkout
- **Then:** A 10% discount is applied to the cart subtotal and shown as a separate line item

**Why This Next:** Member tier is the most common discount segment — covers majority of value before VIP / first-time variations.
**Estimated Effort:** 1.5 days (rule logic + UI display; share infrastructure with 2b/2c)

---

### Story 2b: Apply VIP discount (20%) — Second Business Rule Variation

**Summary:** VIP-tier shoppers receive 20% off cart subtotal.

**Use Case:**
- **As a** VIP-tier shopper
- **I want to** see my 20% VIP discount automatically applied at checkout
- **so that** I receive my premium tier benefit

**Acceptance Criteria:**
- **Given:** I am logged in as a VIP-tier shopper with items in cart
- **When:** I navigate to the discount step
- **Then:** A 20% discount is applied (mutually exclusive with member discount; VIP wins)

**Why This Next:** Premium tier benefits are visible signal of program value; mutex logic with 2a is trivial after 2a built.
**Estimated Effort:** 1 day

---

### Story 2c: Apply first-time discount (5%) — Third Business Rule Variation

**Summary:** First-time buyers receive 5% off their first cart.

**Use Case:**
- **As a** first-time shopper
- **I want to** see my 5% first-time discount applied automatically at checkout
- **so that** I get my onboarding incentive without entering codes

**Acceptance Criteria:**
- **Given:** I have no prior completed orders and items in cart
- **When:** I navigate to the discount step
- **Then:** A 5% first-time discount is applied (stackable with member but not with VIP)

**Why This Next:** Onboarding incentive is acquisition lever; stack rules with 2a/2b finalize the discount engine.
**Estimated Effort:** 1.5 days

---

### Story 3a: Accept Visa payments (Major Effort — First Implementation)

**Summary:** Build payment infrastructure with Visa as the first supported card.

**Use Case:**
- **As a** shopper with a Visa card
- **I want to** complete my purchase by paying with my Visa card
- **so that** I can finalize the order and receive confirmation

**Acceptance Criteria:**
- **Given:** I am at the payment step with a discounted cart
- **When:** I enter Visa card details and click "Pay"
- **Then:** Payment is processed via gateway, order is created, and I receive a confirmation page

**Why This Next:** First payment integration carries 80% of the effort (gateway integration, PCI compliance, error handling). Subsequent cards reuse this infrastructure.
**Estimated Effort:** 5 days (gateway setup + PCI compliance + error handling)

---

### Story 3b: Add Mastercard, Amex support (Major Effort — Trivial Additions)

**Summary:** Extend payment support to Mastercard and Amex.

**Use Case:**
- **As a** shopper with a Mastercard or Amex card
- **I want to** complete my purchase using my preferred non-Visa card
- **so that** I'm not forced to use a Visa card

**Acceptance Criteria:**
- **Given:** I am at the payment step with the Visa flow already shipped
- **When:** I select Mastercard or Amex and complete the payment form
- **Then:** Payment is processed via the same gateway with the additional card type

**Why This Next:** Payment infrastructure exists from 3a; adding card types is configuration, not new infrastructure.
**Estimated Effort:** 1 day (config + UI card selector)

---

## Split Evaluation

✅ **Does this split reveal low-value work?**
- After analysis, **Story 2c (first-time discount)** drives < 5% of orders historically. Consider deferring to Phase 2 or replacing with a better-targeted onboarding mechanism (e.g., welcome email coupon).
- Story 3b's **Amex support** has < 2% Amex card share in target market — could be deferred to Phase 2 if engineering time is tight.

✅ **Does this split produce equally-sized stories?**
- Story 1: 2 days
- Story 2a: 1.5 days
- Story 2b: 1 day
- Story 2c: 1.5 days
- Story 3a: 5 days (intentionally larger — infrastructure pattern; cannot be split further without violating vertical slicing)
- Story 3b: 1 day
- **Total: 12 days across 6 stories**, with 5 of 6 stories in the 1-2 day range. Story 3a is the only outlier and is appropriately sized for its infrastructure scope.

---

## INVEST Validation (Each Story)

✅ **Independent:** Story 1 must precede 2a/2b/2c; 3a must precede 3b; otherwise stories are independently prioritizable.
✅ **Negotiable:** Each story leaves implementation details (UI layout, error message wording, retry logic) to the team.
✅ **Valuable:** Every story (even Story 1 standalone) delivers observable user value; nothing is a pure "technical task".
✅ **Estimable:** All stories sized; only 3a exceeds 5 days due to infrastructure scope.
✅ **Small:** 5 of 6 stories fit in 1-2 days; Story 3a is acceptably sized for its scope.
✅ **Testable:** Each story has Gherkin Given/When/Then acceptance criteria.

---

## Next Steps

1. **Review with team:** Confirm with engineering whether Story 3a's 5-day estimate is realistic given the chosen payment gateway (Stripe vs. Adyen affects complexity).
2. **Check for further splitting:** Story 3a may need to split if estimate climbs above 5 days — restart Pattern 1 on it (e.g., Pattern 8 Defer Performance: ship "Visa works" before "Visa with PCI Level 1 compliance").
3. **Prioritize:** Story 1 → Story 2a → Story 3a (covers 80% of users with member-tier Visa flow). Defer 2b/2c/3b to Phase 2.
4. **Consider eliminating:** First-time discount (2c) and Amex (3b) data suggests deferring to Phase 2 unless business sponsor disagrees.
```

---

## Why This Example Demonstrates the Methodology

- **Pattern cascading**: First pass applied Pattern 1 (Workflow Steps) producing 3 stories; 2 of 3 still > 5 days, so Pattern 3 and Pattern 6 applied to the survivors. This iterative approach is normal — single-pass splits rarely produce all 1-5 day stories.
- **Vertical slicing preserved**: Every story (including Story 1 "Add items to cart") delivers observable user value end-to-end (UI + state + persistence). No horizontal slicing.
- **Major Effort pattern intentionally produces uneven sizes**: Story 3a (5 days) and Story 3b (1 day) are the canonical Major Effort signature — first implementation builds infrastructure, subsequent variants are trivial. Equal sizing is *not* required when infrastructure is the dominant complexity.
- **Split Evaluation reveals waste**: First-time discount (2c, < 5% orders) and Amex (3b, < 2% market share) candidates for deferral or elimination — exactly what good splits should expose.
