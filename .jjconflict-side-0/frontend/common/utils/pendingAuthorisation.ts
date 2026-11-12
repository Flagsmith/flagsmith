// The dashboard hosts the OAuth consent screen (it is the authorization
// endpoint in our RFC 8414 metadata), so a CLI or MCP client that opened it
// while logged out is now blocked on a loopback callback that only this browser
// can answer - and it gives up after a few minutes.
export const AUTHORISE_PATH = '/oauth/authorize'

/**
 * Whether a stored post-login redirect is a consent request waiting to be
 * answered. Compares the whole path so an absolute URL never matches: the
 * redirect is read from a cookie, and this decides where we send the browser.
 */
export const isPendingAuthorisation = (
  redirect?: string | null,
): redirect is string => {
  if (!redirect) return false
  const path = redirect.split('?')[0]
  return path.replace(/\/+$/, '') === AUTHORISE_PATH
}
