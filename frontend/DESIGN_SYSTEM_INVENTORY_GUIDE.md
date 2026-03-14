# Design System Inventory Guide

A practical guide for conducting the Flagsmith frontend interface inventory, based on industry methodology from Brad Frost, Alla Kholmatova, and Nathan Curtis.

## Why an Interface Inventory?

An interface inventory is "a comprehensive collection of the bits and pieces that make up your interface" (Brad Frost). It helps teams:

- Identify visual inconsistencies by seeing similar components side by side
- Establish a shared vocabulary for UI patterns
- Determine the level of effort required to consolidate components
- Define which patterns make the final cut in the design system

In our case, with no dedicated designer on the team, the inventory is owned by the frontend engineer responsible for the design system. This is common — most design systems at this scale are built and maintained by frontend developers (sometimes called design engineers or UI engineers).

## Inventory Process

### Step 1 — Screenshot collection *(in progress)*

Go through the app page by page in both light and dark mode. Capture the default state of each page — don't focus on interactive states yet, those will be covered during the component grouping phase.

Capture both modes for each page:
- **Light mode** — default appearance
- **Dark mode** — reveals broken or missing styles

Main flows to cover:
- Sign in / Sign out
- Projects
- Feature flags list and feature detail
- Segments
- Identities
- Audit log
- Change requests
- Integrations
- Compare
- Release pipelines
- Project settings
- Organisation settings

### Step 2 — Organise by feature area in Penpot *(light mode done)*

Group screenshots into Penpot boards by feature area. Light and dark mode screenshots for the same screen should sit side by side — this makes dark mode gaps immediately visible.

### Step 3 — Break into component categories

Once all pages are captured, go through the screenshots and extract recurring UI patterns into component-focused boards:

| Category | What to capture |
|----------|----------------|
| **Global elements** | Header, navigation, sidebar |
| **Typography** | Headings, body text, labels, links |
| **Buttons** | Every variant found in the wild |
| **Forms** | Inputs, selects, checkboxes, switches, textareas |
| **Icons** | All icons at their actual rendered sizes |
| **Colours** | Backgrounds, text colours, borders, shadows |
| **Cards/Panels** | Content containers |
| **Lists/Tables** | Data display patterns |
| **Modals/Dialogs** | Overlays, confirmations, alerts |
| **Feedback** | Toasts, alerts, empty states, loading states |
| **Navigation** | Tabs, dropdowns, menus, breadcrumbs |

This is where consolidation opportunities become visible — seeing 8 different button styles side by side makes the case for reducing them self-evident.

### Step 4 — Annotate inconsistencies

With components grouped, annotate directly in Penpot:
- "These two buttons look the same but use different spacing"
- "This icon is 16px here but 20px there"
- "This component has no dark mode support"
- "These modals have different padding values"

Cross-reference with the code audit (`DESIGN_SYSTEM_AUDIT.md`) — the audit identifies exact file paths and line numbers for each issue, the visual inventory shows why it matters.

### Step 5 — Define canonical versions

For each category, decide which variant should be the canonical one:
- Which button variants do we actually need?
- What's our spacing scale?
- What are our colour tokens?
- What states must every interactive component support?

## How This Connects to the Code Audit

The code audit (`DESIGN_SYSTEM_AUDIT.md`) provides the **data layer** — file paths, variant counts, hardcoded values, and dark mode gaps. The visual inventory adds the **visual layer** — which is what makes inconsistencies obvious to the whole team.

| Code audit provides | Visual inventory provides |
|---------------------|--------------------------|
| Exact file paths and line numbers | Side-by-side visual comparison |
| Token misuse (hardcoded values) | Spacing/alignment inconsistencies |
| Dark mode coverage gaps | Colour contrast issues visible at a glance |
| Component variant counts | Redundant patterns visible when grouped |
| Consolidation opportunities | The "ideal" version for each pattern |

## References

- **Interface Inventory** — https://bradfrost.com/blog/post/interface-inventory/
- **Conducting an Interface Inventory** — https://bradfrost.com/blog/post/conducting-an-interface-inventory/
- **Atomic Design** by Brad Frost — https://atomicdesign.bradfrost.com/
- **Design Systems** by Alla Kholmatova — https://www.smashingmagazine.com/design-systems-book/
- **Auditing Design Systems for Accessibility** (Deque) — https://www.deque.com/blog/auditing-design-systems-for-accessibility/
- **Inclusive Dark Mode** (Smashing Magazine) — https://www.smashingmagazine.com/2025/04/inclusive-dark-mode-designing-accessible-dark-themes/
- **Color Tokens for Light and Dark Modes** — https://medium.com/design-bootcamp/color-tokens-guide-to-light-and-dark-modes-in-design-systems-146ab33023ac
- **Nathan Curtis's EightShapes articles** — https://medium.com/eightshapes-llc
