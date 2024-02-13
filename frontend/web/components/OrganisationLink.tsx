import { FC, useMemo } from 'react'
import { NavLink } from 'react-router-dom'

import AccountStore from 'common/stores/account-store'
import { useHasPermission } from 'common/providers/Permission'
import Icon from './Icon'

const OrganisationLink: FC = () => {
  const organisation = AccountStore.getOrganisation()

  const { permission: canManageUserGroups } = useHasPermission({
    id: organisation?.id,
    level: 'organisation',
    permission: 'MANAGE_USER_GROUPS',
  })

  const pageLink = useMemo(() => {
    if (!organisation) return null

    if (AccountStore.isAdmin() || canManageUserGroups) {
      return '/organisation-settings'
    }

    return '/projects'
  }, [organisation, canManageUserGroups])

  return (
    pageLink && (
      <NavLink
        id='org-settings-link'
        activeClassName='active'
        className='nav-link'
        to={pageLink}
      >
        <span className='mr-1'>
          <Icon name='layout' width={20} fill='#9DA4AE' />
        </span>
        {'Organisation'}
      </NavLink>
    )
  )
}

export default OrganisationLink
