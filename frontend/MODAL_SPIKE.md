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

## DS Dialog + Drawer (native `<dialog>`)

Two distinct patterns, two components sharing one native-`<dialog>` base
(`useNativeDialog` + shared `Dialog.Header/Body/Footer` slots):

- **`base/Dialog/`** — centred modal, sizes `sm|md|lg|full`.
- **`base/Drawer/`** — right-anchored drawer (replaces the legacy `side-modal`), `width`
  `default|narrow`.

Both own folders + barrels + co-located SCSS (matching `base/CenteredModal`). Storybook:
`documentation/components/Dialog.stories.tsx`, `Drawer.stories.tsx`.

- **Native `<dialog>` + `showModal()`** — top layer (no z-index, no portal target), built-in
  focus trap and Esc, `::backdrop`.
- **Compound API** — `Dialog` + `Dialog.Header` / `Dialog.Body` / `Dialog.Footer`, the shape the
  industry standardises on (Radix, MUI Base, Chakra).
- **Tokenised chrome** — `--color-surface-*` / `--color-border-*` / radius, so it themes
  light/dark with no bootstrap dependency.
- **Declarative** — the parent owns `open`; `onClose` fires on Esc, backdrop click, and the close
  button. New modal code can use `Dialog` or `Drawer` directly today.

### Sequence

1. **DS `Dialog` component** — done. Usable for new declarative modals.
2. **Point the imperative manager at `Dialog`** — done. `ModalManager` renders `Dialog`
   (default stack + inline confirm) instead of reactstrap. `interceptClose` and `setModalTitle`
   moved to the controller (the manager honours them); `ModalDefault` is a re-export shim;
   `ModalConfirm` removed. `openModal`/`openModal2`/`openConfirm` signatures unchanged.
3. **Other reactstrap consumers migrated + `side` split into `Drawer`** — done.
   `IntegrationSelect`, `useFormNotSavedModal`, `CenteredModal` use `Dialog`; the manager routes
   legacy `side-modal` to `Drawer`. `ModalDefault`/`ModalConfirm` are deleted and the guard/title
   helpers moved to the controller. The reactstrap `<Modal>` portal is gone from the modal path
   (reactstrap's `ModalBody`/`ModalFooter` helper divs still appear in modal *content* — dropping
   the dep entirely is a separate follow-up).
4. **Variant CSS migrated** — done (but unverified). `_modals.scss` retargeted from bootstrap's
   `.modal-dialog`/`.modal-content`/`.modal-body` to the new `.dialog__panel`/`.dialog__body`;
   the legacy `openModal` className (`side-modal`, `create-feature-modal`, `p-0`, `modal-full-screen`)
   passes through to the dialog element, so those hooks still land. Dead reactstrap-portal rules
   removed, colours moved to `--color-*` tokens (the `.dark` overrides drop out). Content JSX is
   unchanged — standard `.modal-footer` divs keep bootstrap's base styling inside `Dialog.Body`.
   Animations (fade-up / drawer slide) done via `@starting-style`.

The only thing left is **runtime QA** — this CSS was written without a browser, so the
`create-feature` drawer (absolute tab-height calcs) and general visual parity need checking
against a running app.

### QA checklist (needs a dev server)

- [ ] Plain modals open/close: Esc, backdrop click, close button, and programmatic `closeModal()`.
- [ ] `openConfirm` yes/no + destructive styling.
- [ ] Stacked `openModal2` on top of a modal (z-index via the top layer).
- [ ] Unsaved-changes guard (`interceptClose`) on create/edit modals.
- [ ] Dynamic title (`setModalTitle`) in create-feature / create-experiment.
- [ ] **side-modal / create-feature drawer** — layout, tabs, height calcs (the hotspot).
- [ ] Padding parity vs the old `$modal-*-padding` tokens; dark mode.
- [ ] `.modal-open` body effects: scroll lock, support-chat hidden.
- [ ] E2E modal-heavy flows + Chromatic.

## Effort

Small-to-medium: the base is done here. Remaining is runtime QA across the modal surface
(~35 modal components), removing the dead template roots, simplifying the `.hljs` scope, and
the CSS variant re-mapping above (which dominates).
