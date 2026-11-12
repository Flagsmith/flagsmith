import { User } from 'common/types/responses'

export const ORGANISATION_ADMIN_ROLE = 'ADMIN'

export const isOrgAdmin = (user: Pick<User, 'role'>) =>
  user.role === ORGANISATION_ADMIN_ROLE
