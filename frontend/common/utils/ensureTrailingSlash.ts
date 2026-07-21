export const ensureTrailingSlash = (url: string): string =>
  url && !url.endsWith('/') ? `${url}/` : url
