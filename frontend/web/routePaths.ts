import { matchPath } from 'react-router-dom'

// Kept out of web/routes, which imports App: reading a path from there in a
// component is a cycle, and it took the app down once.
export const ORGANISATIONS = '/organisations'
export const ORGANISATION_USAGE = '/organisation/:organisationId/usage'

// A blocked organisation keeps the organisations list, to switch away, and the
// usage page, which explains the block.
const ALLOWED_WHILE_BLOCKED = [ORGANISATIONS, ORGANISATION_USAGE]

export const isAllowedWhileBlocked = (pathname: string): boolean =>
  ALLOWED_WHILE_BLOCKED.some((path) =>
    matchPath(pathname, { exact: true, path, strict: false }),
  )
