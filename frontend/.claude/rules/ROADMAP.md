# Design system — open roadmap items

Known gaps in the token system. Each item should be evaluated as its own discrete piece of work — do not let the rules absorb pressure to paper over missing tokens.

## 1. Semantic spacing tokens

**Gap.** Flagsmith has no semantic spacing token layer (no `--space-*` custom properties, no `$space-inset-*` / `$space-stack-*` SCSS aliases). Spacing is currently expressed via Bootstrap 5 utility classes (`p-3`, `gap-3`, `mb-4`) backed by the `$spacers` map.

**Why it matters.** Without semantic aliases, the auditor can enforce "value is on the scale" but not "intent matches named token." We cannot require `$space-inset-lg` on a card, only that the resolved value is 16px — which is a weaker check.

**Proposed work (out of scope for this PR).**

1. Add a semantic layer in `common/theme/tokens.json` — `space-inline-{xs,sm,md}`, `space-stack-{xs,sm,md,lg}`, `space-inset-{sm,md,lg,xl}`, `space-section-{sm,md}`, `space-gutter`, `space-page-x`. Map each to a multiple of `$spacer` / the existing scale.
2. Regenerate `_tokens.scss` via the existing generator script.
3. Add matching SCSS aliases in `_variables.scss` that also resolve to the same values so legacy SCSS consumers can migrate.
4. Update `spacing.md` to prefer the semantic aliases and mark the raw Bootstrap utilities as "acceptable but less specific."

**Estimated impact.** Additive (no consumer breakage). ~1–2 hours including generator tweaks.

## 2. Semantic typography tokens

**Gap.** Flagsmith has raw size vars (`$h1-font-size` … `$h6-font-size`, `$font-size-base`, `$font-caption*`) and a `$font-sizes` map, but no role-named tokens like `$font-body`, `$font-heading-m`, `$font-overline`. The rules point at the raw vars, which works but is less enforceable.

**Proposed work (out of scope for this PR).**

1. Define a semantic type scale in `tokens.json` — `text-display-{l,m}`, `text-heading-{xl,l,m,s,xs}`, `text-body-{l,default,s,xs}`, `text-caption`, `text-overline`, `text-code`. Each token carries size + line-height + weight + letter-spacing.
2. Generate SCSS mixins so consumers can `@include text-body-default;` instead of setting three properties separately.
3. Update `typography.md` to prefer the semantic names.

**Estimated impact.** Additive. The most value comes when auditors can assert "a card title is `text-heading-m`" rather than "its font-size is 18px and weight is 600."

## 3. Finer-grained spacing scale

**Gap.** Bootstrap 5's default scale is `0 / 4 / 8 / 16 / 24 / 32`. This omits 12, 20, 40, 48, 64 — all of which show up in real dashboards (row heights, section breathers, KPI tile minimums). Designers currently reach for `$spacer * 0.75` or literal px values because the utility scale doesn't cover the gap.

**Proposed work (out of scope for this PR).**

1. Extend the Bootstrap `$spacers` map with additional steps: `$spacer * 0.75` (12), `$spacer * 1.25` (20), `$spacer * 2.5` (40), `$spacer * 3` (48), `$spacer * 4` (64).
2. Keep existing keys (`0/1/2/3/4/5`) unchanged to avoid breakage. Add new keys (e.g., `6 = 40px`, `7 = 48px`, `8 = 64px`; interstitial `3h = 20px`, `2h = 12px` where valid SCSS keys permit — may need renaming to `xs/sm/md/lg/xl`-style keys if Bootstrap utility generation doesn't accept non-integer keys).
3. Audit consumers. The Bootstrap utility generator auto-produces new class names (`m-6`, `p-6`, `gap-6`) — check for class-name collisions in existing code.
4. Only after (1)–(3) land: consider adding a 4 × 4px semantic step system (`space-1` … `space-24`, 16 tiers) to align with the Obsidian reference scale. This is the larger migration.

**Estimated impact.** Additive if done carefully. The utility-class key question determines whether this is a 1-hour or a 1-day change.

## 4. AI summary block pattern

Not currently an established Flagsmith pattern. `components.md` documents a proposed spec. Decide before the rule calcifies: do we want AI surfaces in this product, and if so, does the proposed spec (info-tinted surface + sparkle icon + "AI Summary" label + disclaimer) match the intended visual language?

## Not doing (explicit)

- **Pink/coral brand gradient** — Flagsmith is solid purple. The Obsidian `--bs-brand-gradient` pattern was deliberately removed from all ported rules.
- **Six-tier motion duration scale** — Flagsmith's 3-tier (fast/normal/slow) system is simpler and correct for a dual-mode product dashboard. Do not port Obsidian's `$transition-slower / -slowest` unless a real spatial-movement transition needs >300ms.
- **Dark-only colour reasoning** — all rules are dual-mode. Do not add "on dark mode…" conditionals to rule prose; the tokens handle it.
