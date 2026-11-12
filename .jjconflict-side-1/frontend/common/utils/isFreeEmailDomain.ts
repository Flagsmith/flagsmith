import freeEmailDomains from 'free-email-domains/domains.json'

export default function (value: string | null | undefined) {
  if (!value) return false
  const domain = value?.split('@')?.[1]
  return freeEmailDomains.includes(domain)
}
