// Storybook stub for common/utils/utils.
// The real Utils has circular dependencies (utils → account-store → constants)
// that crash webpack in Storybook.
// Only legacy .js components (Input.js) depend on this global.
// New components should NOT import Utils — use dedicated utilities instead.
// TODO: Remove once legacy .js files are migrated to TypeScript with imports.

const Utils = {
  getFlagsmithHasFeature: () => false,
  getFlagsmithValue: () => '',
  getPlansPermission: () => true,
  keys: {
    isEscape: (e) => e.key === 'Escape' || e.keyCode === 27,
  },
  safeParseEventValue: (e) =>
    e?.target?.value !== undefined ? e.target.value : e,
}

export default Utils
