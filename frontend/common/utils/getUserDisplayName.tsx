import { User } from 'common/types/responses'

export default function (user: User | undefined, defaultName = 'Unknown') {
  if (!user) {
    return defaultName
  }
  if (user?.first_name || user?.last_name) {
    return `${user?.first_name} ${user?.last_name}`
  }
  return user?.email || defaultName
}
