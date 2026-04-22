# Rule: copy and voice (Flagsmith)

Flagsmith uses British English per `AGENTS.md` — "colour", "organise", "behaviour", "centre", "favourite", "utilise" (prefer "use"). Keep sentence-case headings and verb-first buttons.

A pixel-perfect component with bad copy is still a bad component.

Most copy findings are `minor`. Escalate to `major` when: error messages blame the user; buttons use forbidden generics ("OK", "Submit"); tech-bro vocabulary appears in user-facing copy.

Rules marked **[manual review]** cannot be auto-checked.

---

## 1. Case

### Sentence case everywhere (default)

Headings, button labels, menu items, table headers, badges, chips — all sentence case.

- OK: "Add environment"
- OK: "No flags yet"
- OK: "Billing and subscription"
- Bad: "Add Environment"
- Bad: "No Flags Yet"
- Bad: "Billing And Subscription"

### Exceptions (only)

- **Proper nouns** keep their case: "Flagsmith", "GitHub", "Azure".
- **Acronyms** stay uppercase: "API", "SDK", "SSO", "SAML".
- **Code** and **identifiers** preserve exact case: `useFlag`.
- **Overline tokens** (11/16 600 UPPERCASE label style) are ALL CAPS — labels, not copy.

### Never

- **ALL CAPS for emphasis** — use weight or colour.
- **Title Case For Headings**.
- **Sentence case applied to proper nouns**.

### What the auditor checks

- Heading / button / menu / table-header text isn't Title Case — flag if >60% of words start with uppercase excluding known proper nouns/acronyms (auto, `medium`).
- No `text-transform: uppercase` on elements not using the overline style (auto).

---

## 2. Descriptor length

| Context | Target | Maximum |
|---|---|---|
| Section descriptor | 1 sentence, 10–20 words | 2 sentences, 35 words |
| Card descriptor | 5–12 words | 1 short sentence |
| Empty state descriptor | 1–2 sentences, explain what + suggest action | 3 sentences |
| Help text under input | 3–8 words | 1 short sentence |
| Modal intro | 1–2 sentences | 3 sentences |

**Rule.** If a descriptor needs more than 2 sentences, the heading isn't specific enough. Fix the heading, not the descriptor.

### Content

1. **State the facts, then the action.** "Your tracked flags and their rollout percentages." beats "View and manage all your flags."
2. **Specificity beats generality.** "Last 30 days of flag rollout changes" beats "Your flag data."
3. **Numbers when informative.** "Across 142 environments" anchors the reader.
4. **No marketing fluff.** "Unlock powerful insights" is noise.

### Voice

- **Second person** ("you", "your") for actions and user data.
- **Third person** for system descriptions ("The scan runs daily.").
- **First-person plural ("we/our")** permitted in onboarding, release notes, help copy where personification helps. Avoid in dense UI chrome.

### What the auditor checks

- Descriptor word count within target for its context (auto).
- **[manual review]** descriptors are specific.
- Descriptor does not start with marketing verbs (`Unlock`, `Stay`, `Supercharge`, `Crush`, `Dominate`) — auto, `minor`.

---

## 3. Numbers and units

### Digits vs words

- **Digits always** for numeric data, counts, currency, percentages, dates, times, durations.
- **Words** in prose only for numbers 0–9 that aren't data ("two reasons why").

### Formatting

| Type | Format | Example |
|---|---|---|
| Integer | Localised separator | `1,234` |
| Decimal | Match precision to context | `12.4%`, `£1,234.56` |
| Percentage | 1 decimal unless whole | `12.4%`, `50%` (not `50.0%`) |
| Currency | Symbol before, 2 decimals; localised for non-£ currencies | `£99.00`, `$99.00`, `€99,00` |
| Large numbers | Abbreviate ≥1,000 in KPIs | `1.2M`, `4.5K` |
| Negatives | Minus sign, not parens | `-£50` (not `(£50)`) |

### Units

- **Space between number and unit** for time/size/distance: `5 min`, `240 px`, `2 km`.
- **No space for currency, percentage, degrees**: `£50`, `12%`, `45°`.
- **Unit plurals lowercase**: `mins`, `hrs`, `days`. Pick one form per view.
- **Abbreviate consistently**: always `ms`, always `s`.

### Time

- **Relative time** for recency: "2m ago", "3h ago", "yesterday".
- **Absolute time** for specificity: "Mar 14, 2026 at 3:45 PM".
- **Both in tooltips**: visible relative, `title` for absolute.
- **Durations**: "2 min", "1 hr 30 min" — not "2m" outside relative-time.

### What the auditor checks

- Percentages use 1 decimal unless whole (auto).
- Currency formatted with symbol and correct decimals (auto).
- Large KPI numbers abbreviated (auto — raw `1234567` in a KPI is a finding).
- Unit formatting consistent within a view (auto).
- **[manual review]** relative vs absolute time choice.

---

## 4. Abbreviations

### Always abbreviate

- Common tech terms: API, URL, HTML, CSS, JS, JSON, CSV, PDF, UI, UX, AI, ML, SDK.
- Product-specific acronyms: SSO, SAML, RBAC.
- Time units in dense contexts: ms, s, min, hr, d.
- Date abbreviations in dense contexts: Jan, Feb.

### Never abbreviate

- Product features (unless the abbreviation is the product name).
- Action verbs: never "Del." for Delete, "Edt." for Edit.
- Status labels: "Active", "Paused", "Error" — not "Act.", "Paus.", "Err."

### Usage rules

1. **First use in a page defines the term**: "Single Sign-On (SSO)" — then SSO afterwards.
2. **Exception**: product-established acronyms (API, SDK, KPI) don't need spelling out.
3. **Ampersand `&`** in brand / product names only. In copy, write "and".
4. **`&` in table headers** is acceptable when space-constrained.

### What the auditor checks

- Acronyms used consistently (auto — two spellings of same term = finding).
- No excessive abbreviation of action verbs (auto — flag buttons matching `/^[A-Z][a-z]{1,3}\.?$/`).
- **[manual review]** acronym familiarity to audience.

---

## 5. Button labels

### Format

- **Verb-first**: "Add environment", "Export data", "Save changes".
- **Specific**: "Save changes" beats "Save"; "Delete organisation" beats "Delete".
- **1–4 words**.
- **Consistent across the product**: don't have "Add" here and "Create" there for the same action type.

### Never

- **One-word generic verbs**: "OK", "Submit", "Go". Specific or nothing.
- **Button text asking a question**: "Do you want to save?" is a dialog, not a button.
- **Sentence fragments**: "In the event you...".

### Destructive buttons

- Specify the consequence: "Delete 12 environments" rather than "Delete".
- Require confirmation modal for irreversible actions.
- Confirmation button echoes the destructive verb: `Cancel | Delete 12 environments` — not `Cancel | OK`.

### Loading / disabled

- Loading: replace leading icon with spinner; keep label (avoid "Saving…" — shifts layout).
- Disabled: label stays; tooltip explains why.

### What the auditor checks

- Button labels verb-first (auto; flag noun/adjective-first, `medium`).
- Primary button labels not in the forbidden-generic set — auto, `major`.
- Button labels 1–4 words (auto; flag >4).
- Destructive buttons specify a count or object (auto — bare "Delete" in a confirmation modal is a finding).
- **[runtime]** confirmation modals exist for destructive actions.

---

## 6. Form copy

### Labels

- Sentence case, 1–3 words: "Email address", "Full name", "API key".
- Required fields marked with asterisk after label: "Email *".
- Optional fields labelled: "Company (optional)".
- **Never "Please enter your..."** — the label is the instruction.

### Placeholders

- **Placeholders are examples, not instructions.** The label handles instruction.
- Format: `e.g. example@domain.com` or `Like "Acme Inc"`.
- Never use placeholders in place of labels.
- Placeholder colour is `var(--color-text-disabled)`.

### Helper text

- Short: "3–20 characters", "Shown on your public profile".
- Below the field in 11/16 `var(--color-text-secondary)`.
- Doesn't repeat the label.

### Errors

- **Specific**: "Email must include @" rather than "Invalid email".
- **Actionable**: tell the user what to do.
- **Polite, not accusatory**: "This email is already in use — [sign in instead?]" rather than "Email already taken, try again".

### What the auditor checks

- Labels in sentence case, 1–3 words (auto).
- Required fields marked (auto).
- Optional fields labelled when form has ≥1 required field (auto).
- Placeholders are examples (start with `e.g.` or `Like`) not instructions (auto, `minor`).
- Placeholder colour resolves to `var(--color-text-disabled)` (auto).
- **[manual review]** error messages specific and actionable.

---

## 7. Inclusive and clear language

### Avoid jargon unless familiar

Use with glossary support or initial definitions when audience may not know the term.

### Avoid tech-bro vocabulary

- Bad: "Crush your goals", "Unleash your potential", "Dominate the market".
- Bad: "Ninja", "rockstar", "10x".
- Good: Plain language.

### Avoid gendered language

- Use "they/them" for generic users.
- "Teammates" rather than "guys".

### Avoid "simply" and "just"

- Bad: "Simply click the button" — condescending if true, a lie if not.
- Bad: "Just add your API key" — implies obviousness the user may not share.

### "Please" in commands

Usually unnecessary. "Enter your email" beats "Please enter your email". Exception: error and permission states where politeness helps ("Please try again in a few minutes") is fine.

### What the auditor checks

- Flag tech-bro tokens (`ninja`, `rockstar`, `10x`, `unleash`, `dominate`, `crush`) — auto, `major`.
- Flag `simply` and `just` as softening hedges (auto, `minor`).
- **[manual review]** plain language appropriate to audience.
- **[manual review]** tone direct and respectful.

---

## Copy auditor walk

1. **Case** — sentence case with exceptions, no ALL CAPS outside overline.
2. **Descriptor length and quality** — specific, explanatory, target length.
3. **Numbers and units** — digits for data, consistent formatting, appropriate precision.
4. **Acronyms and abbreviations** — defined on first use, used consistently.
5. **Button labels** — verb-first, specific, destructive buttons specify consequence.
6. **Form labels, placeholders, errors** — labels above fields, placeholders as examples, errors specific.
7. **Voice** — direct, respectful, plain language, British spelling.
8. **Primary-label readability** — every interactive element's label understandable without context.

Confidence:

- **High**: verifiable from explicit rules (case, format, required-field asterisks).
- **Medium**: pattern match (descriptor specificity, button verb-first-ness).
- **Low**: [manual review] tone and voice.
