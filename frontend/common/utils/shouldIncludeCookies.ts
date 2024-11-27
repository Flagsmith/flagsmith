import Project from 'common/project'

export default function includeCookies() {
  if (Project.cookieAuthEnabled) {
    return true
  }
  if (!global.flagsmithVersion?.backend?.is_saas) return false
  // Extract the base domain
  const getBaseDomain = (url: string) => {
    const hostname = new URL(url).hostname
    const parts = hostname.split('.')
    return parts.slice(-2).join('.')
  }

  const originBaseDomain = getBaseDomain(document.location.origin)
  const projectApiBaseDomain = getBaseDomain(Project.api)

  return originBaseDomain === projectApiBaseDomain
}
