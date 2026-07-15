// Integrations whose backend wrapper appends a path directly to base_url,
// so the value must end with a slash (e.g. NewRelicWrapper builds
// `{base_url}v2/applications/...`). Presets are slash-terminated already;
// this guards custom URLs typed by the user.
const TRAILING_SLASH_INTEGRATIONS = new Set(['new-relic'])

export const normaliseIntegrationBaseUrl = (
  integrationId: string,
  formData: Record<string, any>,
): Record<string, any> => {
  if (!TRAILING_SLASH_INTEGRATIONS.has(integrationId)) {
    return formData
  }
  const baseUrl = formData.base_url
  if (typeof baseUrl !== 'string' || !baseUrl || baseUrl.endsWith('/')) {
    return formData
  }
  return { ...formData, base_url: `${baseUrl}/` }
}
