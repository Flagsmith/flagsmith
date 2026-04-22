# Rule: motion (Flagsmith)

Flagsmith's motion system is a tight three-tier duration scale plus three easings. See `design-tokens.md`.

## Durations

```
--duration-fast    100ms   hover, focus ring, press
--duration-normal  200ms   dropdowns, tooltips, tabs (default)
--duration-slow    300ms   modals, drawers, sheets
```

Anything over 300ms must earn it with explicit keyframes and real spatial movement — there is no token beyond `--duration-slow`.

Skeleton shimmer is a loop, not a UI transition: use a literal `1800ms` in the keyframes; do not add a token for it.

## Easing

```
--easing-entrance  cubic-bezier(0.0, 0, 0.38, 0.9)   enter
--easing-exit      cubic-bezier(0.2, 0, 1.0, 0.9)    exit
--easing-standard  cubic-bezier(0.2, 0, 0.38, 0.9)   default / reorder
```

No Material-3 "emphasised" tier. If an interaction wants more punch, use `--easing-entrance` on enter and accept the system's simpler 3-tier model.

## Prescribed combinations

| Interaction | Duration | Easing |
|---|---|---|
| Hover colour / bg shift | `--duration-fast` | `--easing-standard` |
| Button press | 80ms | `--easing-exit` |
| Focus ring appear | `--duration-fast` | `--easing-entrance` |
| Tooltip in / out | `--duration-fast` / 80ms | `--easing-entrance` / `--easing-exit` |
| Dropdown in / out | `--duration-normal` / `--duration-fast` | `--easing-entrance` / `--easing-exit` |
| Tabs indicator slide | `--duration-normal` | `--easing-standard` |
| Toast in / out | `--duration-normal` / `--duration-fast` | `--easing-entrance` / `--easing-exit` |
| Modal in / out | `--duration-slow` / `--duration-normal` | `--easing-entrance` / `--easing-exit` |
| Drawer enter | `--duration-slow` | `--easing-entrance` |
| Page transition | `--duration-slow` | `--easing-standard` |
| Skeleton shimmer | 1800ms | linear infinite |
| Number count-up | 400–600ms | `--easing-entrance` |

## Rules

1. **90% of UI transitions ≤ 200ms.** Anything ≥ 300ms earns it through real spatial movement.
2. **Exit faster than enter** (~0.7× ratio). Entering teaches a relationship; exiting gets out of the way.
3. **Never animate live data.** Tables, KPIs, charts updating from a stream do not transition. A single 300ms `var(--color-surface-action-subtle)` flash on the changed cell is permitted.
4. **Never animate mission-critical UI** — error toasts, security prompts, validation errors. Instant.
5. **Respect `prefers-reduced-motion`:**

```css
@media (prefers-reduced-motion: reduce) {
  .modal, .drawer, .popover, .toast, .sheet {
    transform: none !important;
    transition: opacity 120ms linear !important;
  }
  .skeleton-shimmer, .marquee, .parallax, .spinner-decorative {
    animation: none !important;
  }
}
```

## Common violations

- `transition: all 0.5s ease` — too long, wrong easing, `all` is a performance bug.
- Raw duration `200ms` — use `var(--duration-normal)`.
- Raw easing string `cubic-bezier(...)` — use a named `--easing-*` token.
- Animating table row updates from a live stream.
- Missing `prefers-reduced-motion` media query on transform-heavy components.
- Spinner shown for operations <300ms (causes flash-flicker — delay by 300ms).
- Using a transition longer than `--duration-slow` (300ms) without explicit keyframes and a spatial reason.
