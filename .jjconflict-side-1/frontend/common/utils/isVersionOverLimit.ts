import moment from 'moment'

// True when a version is older than the plan's feature history limit.
export function isVersionOverLimit(
  versionLimitDays: number | null | undefined,
  date: string | undefined,
) {
  if (!versionLimitDays) {
    return false
  }
  const days = moment().diff(moment(date), 'days') + 1
  return !!versionLimitDays && days > versionLimitDays
}
