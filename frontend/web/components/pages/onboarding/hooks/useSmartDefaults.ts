import { useMemo } from 'react'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'

export type SmartDefaults = {
  orgName: string
  projectName: string
}

const titleCase = (value: string): string =>
  value
    .split(/[-._\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')

export const orgNameFromEmail = (email: string, firstName: string): string => {
  if (!email || !email.includes('@')) {
    return firstName ? `${firstName}'s Org` : ''
  }
  const domain = email.split('@')[1] ?? ''
  if (!domain || isFreeEmailDomain(`@${domain}`)) {
    return firstName ? `${firstName}'s Org` : ''
  }
  const root = domain.split('.')[0] ?? ''
  return root ? titleCase(root) : ''
}

export const useSmartDefaults = (
  email: string,
  firstName: string,
): SmartDefaults =>
  useMemo(
    () => ({
      orgName: orgNameFromEmail(email, firstName),
      projectName: 'My first project',
    }),
    [email, firstName],
  )
