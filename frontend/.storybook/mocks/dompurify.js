// Mock for dompurify — the real module's CJS/ESM export mismatch breaks Storybook.
// Tooltip only uses sanitize() to clean HTML before rendering.
export function sanitize(html) {
  return html
}

export default { sanitize }
