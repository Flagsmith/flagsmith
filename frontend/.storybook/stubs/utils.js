// Storybook stub for common/utils/utils.
// The real Utils has circular dependencies (utils → account-store → constants)
// that crash webpack in Storybook. This provides the minimal API that
// components actually call at runtime.
const Utils = {
  keys: {
    isEscape: (e) => e.key === 'Escape' || e.keyCode === 27,
  },
  safeParseEventValue: (e) =>
    e?.target?.value !== undefined ? e.target.value : e,
  getFlagsmithHasFeature: () => false,
  getFlagsmithValue: () => '',
  getPlansPermission: () => true,
}

export default Utils
