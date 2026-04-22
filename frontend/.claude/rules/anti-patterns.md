# Rule: anti-patterns — what never to ship (Flagsmith)

The auditor treats every item below as an automatic finding.

## Colour

1. Pure `#000` as background.
2. Pure `#FFFFFF` as body text colour.
3. Raw hex in product code (`color: #1a2634`) — must be `var(--color-text-default)`.
4. Primitive SCSS vars in components (`color: $slate-600`) — must be a semantic CSS custom property.
5. `color: white` as default body text in a dual-mode component — won't flip in light mode.
6. `.dark` selector override in a component to "fix" a colour — fix the token in `_tokens.scss`, don't override per-component.
7. Mixing CSS custom properties and SCSS semantic vars for colour in the same file.
8. Decimal alpha literals: `rgba(0,0,0,0.08)` → `var(--color-surface-hover)` or `$black-alpha-8`.
9. Primary CTA using anything other than `var(--color-surface-action)` fill.
10. Colour-alone state signalling (no icon, no sign, no text).
11. `var(--color-text-tertiary)` on a body paragraph — must be `--color-text-secondary` or `--color-text-default`.
12. Warning / info body-size text on `--color-surface-default` without an icon or tinted fill (fails AA).

## Typography

13. More than three font weights in product UI.
14. Weight 300 below 24px.
15. Weight 800 anywhere in app chrome.
16. Weight 700 as a standalone heading weight — use 600.
17. Body text below 12px.
18. Raw `font-weight: 500` in SCSS — must be `$font-weight-medium`.
19. `tabular-nums` applied to prose or headings.
20. Negative letter-spacing on body text <16px.
21. Missing `tabular-nums` on numeric table cells.
22. `font-size: 15px` / 17px / 22px — off the scale. Pick the nearest scale value.

## Spacing

23. Pixel values outside the Bootstrap scale (`padding: 13px`, `margin: 15px`, `padding: 20px`).
24. `margin` used between flex / grid siblings where `gap` would work.
25. Hand-written `margin-top: 4px` when `mt-1` exists.
26. Page horizontal padding that varies across pages in the same shell.
27. `margin: 10px 15px` — arbitrary composite. Break into utilities.

## Sizing and radii

28. Target size under 24×24px.
29. Radius values bypassing the scale — `border-radius: 7px`. Use `var(--radius-*)`.
30. Radii above `var(--radius-2xl)` (18px) in product chrome.
31. `border-radius` on a `<table>` with `border-collapse: collapse` (silently broken).

## Borders and shadows

32. Zebra stripes + row borders combined. Pick one.
33. Shadow-only elevation. Must combine with surface-lightness shift + 1px `var(--color-border-default)` rim.
34. White or inverted shadows.
35. `var(--color-border-disabled)` as sole separation between surfaces (fails 3:1).

## Interactive states

36. `outline: none` without replacement focus indicator.
37. Bare `:focus` instead of `:focus-visible`.
38. Focus ring thinner than 2px.
39. Focus ring colour not `var(--color-border-action)`.
40. Multiple focus rings visible simultaneously.
41. Disabled state below 3:1 contrast communicating critical info (decorative only).
42. Icon-only button without `aria-label`.
43. Truncation (`text-overflow: ellipsis`) without tooltip or expand affordance.

## Motion

44. Raw duration (`transition: 200ms`) — must be `var(--duration-*)`.
45. Raw easing string — must be `var(--easing-*)`.
46. Hover transitions >200ms.
47. Transition longer than `--duration-slow` (300ms) without keyframes and a spatial reason.
48. Live-data animation (counters, KPIs, table rows transitioning on stream updates).
49. `transition: all` — performance bug, always specify properties.
50. Spinner rendered without 300ms delay for short operations.
51. Missing `prefers-reduced-motion` handling on transform-heavy components.

## Layout

52. Fixed pixel widths on text containers (breaks 200% zoom).
53. Max-width on prose exceeding 65ch.
54. Modal inside a modal.
55. Horizontal page scroll at 375, 768, or 1024 viewports.

## Chart and data viz

56. More than six colours in one chart.
57. White as sequential-scale midpoint (disappears in light mode or punches through in dark).
58. Chart series colour resequenced from the canonical 1–10 palette without a review.

## Accessibility

59. Body text below 4.5:1 contrast in either mode.
60. Non-text UI affordance below 3:1 contrast.
61. Non-keyboard-reachable interactive element.
62. Missing focus trap in modal.
63. Missing skip-link at page top.
64. Missing `aria-live` region for async-updated content.
