# Spike: modal mounting via in-tree portals

## Question

Our modals mount as **separate React roots** — `Modal.tsx` does `createRoot` on the
`#modal`/`#modal2`/`#confirm` divs and wraps each in its own `<Provider store={getStore()}>`.
They're detached trees outside `#app`, which forces per-root store wiring and means CSS
(like the shared `.hljs` theme) has to know about four roots.

Can we move modals into the app's React tree **without touching the ~177 call sites**
(`openModal` ×118, `openConfirm` ×44, `openModal2` ×15)?

## Answer: yes, and it's contained

The migration lives entirely in `web/components/modals/base/` plus one mount point:

- **`modalController.ts`** — module-level modal state + subscribe. `openModal`/`openModal2`/
  `openConfirm` keep their exact signatures and still populate the `window.*`/global bindings,
  so call sites and `main.js` are untouched. Default modals are held as a **stack**, so
  "modal on modal" (old `openModal2`) is just depth 2 of one list, not a bespoke root.
- **`ModalManager.tsx`** — subscribes via `useSyncExternalStore` and renders the active modals.
  Mounted **once** in `App.js` inside the existing `<Provider>`.
- **reactstrap's `container` prop** (default `'body'`) is pointed at `#app`, so the modal DOM
  lands **inside the app root** while React context flows down the tree.
- `Modal.tsx` now just re-exports from the controller.

Net deletion: the per-root `createRoot`, the `withModal` HOC, and the `<Provider>` re-wrap.

## Proven / not yet

- **Proven:** typechecks clean; API and globals preserved; stack supports arbitrary depth;
  each level keeps its `closeModal`/`closeModal2` global by position.
- **Needs a dev-server smoke test:** open/close transitions, the value-editor modal
  inheriting store/theme, DOM landing in `#app`, stacked-modal z-index, and the
  `interceptClose` (unsaved-changes) guard.

## Payoffs

- Modals inherit store/theme/router context — no more `<Provider store={getStore()}>` per root.
- Modal DOM lives under `#app`, so the `:where(#app, #modal, …)` scoping added for the shared
  `.hljs` theme collapses to `#app` alone. The extra template roots become removable.
- `modal2` stops being a special case.

## Risks / open questions

- reactstrap 9 `container='app'` behaviour under stacking (backdrop, scroll-lock on `<body>`).
- Esc-close (#4234) — reactstrap's `toggle` should now behave consistently; worth checking if
  this fixes it.
- `openModal` resets the stack (dismisses a stacked `modal2`); the old code left `#modal2`
  independent. Believed harmless, needs confirming against call sites.
- Fully declarative slots (`<Dialog open>`) remain the long-term target; they'd touch call
  sites and are out of scope for this contained step.

## How the industry does this

A survey of modern React practice and established design systems (MUI, Radix/shadcn, Ant,
Chakra v3, React Aria, Polaris, Carbon, Atlassian) puts this approach in the mainstream:

- **Portal into a configurable container is the norm.** Radix (`Portal container`), MUI
  (`container`), Ant (`getContainer`), Chakra v3 all expose a per-instance target that defaults
  to `<body>`. reactstrap's `container` is the same lever; pointing it at `#app` is a standard move.
- **Our controller is essentially `@ebay/nice-modal-react`.** That library is the reference
  pattern for an imperative "open from anywhere" API over an in-tree provider (promise-based,
  addressable by id, ~2KB). If we would rather not maintain our own controller, adopting it is a
  credible off-the-shelf swap. Trade-off: its `show(id, props)` API differs from our `openModal`,
  so it is not a drop-in for the untouched-call-sites goal.
- **Imperative APIs are the minority.** Most systems are declarative-only (`<Dialog open>`);
  the fully declarative slot approach (`<Dialog open>` rendered in place) is the long-term target
  but touches every call site — out of scope here.
- **If reactstrap is ever replaced, use a headless primitive** (Radix / React Aria) rather than
  hand-rolling focus-trap, scroll-lock, and ARIA.
- **The 2026+ frontier is native `<dialog>` + top layer** (~96% support; Atlassian is migrating
  behind a flag). It makes stacking and z-index free, which would retire our manual modal stack.

Sources: [react.dev createPortal](https://react.dev/reference/react-dom/createPortal),
[nice-modal-react](https://github.com/eBay/nice-modal-react),
[Radix Dialog](https://www.radix-ui.com/primitives/docs/components/dialog),
[caniuse dialog](https://caniuse.com/dialog).

## Effort

Small-to-medium: the base is done here. Remaining is runtime QA across the modal surface
(~35 modal components), removing the dead template roots, and simplifying the `.hljs` scope.
