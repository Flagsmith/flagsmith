import React, { FC } from 'react'
import NavSubLink from 'components/navigation/NavSubLink'
import { apps, statsChart } from 'ionicons/icons'
import Utils from 'common/utils/utils'
import UsersIcon from 'components/icons/UsersIcon'
import {
  useCurrentOrganisation,
  useIsOrganisationAdmin,
} from 'common/hooks/useCurrentOrganisation'
import Project from 'common/project'
import Icon from 'components/icons/Icon'
import OverflowNav from 'components/navigation/OverflowNav'
import AuditLogIcon from 'components/icons/AuditLogIcon'

type OrganisationNavType = {}

const OrganisationNavbar: FC<OrganisationNavType> = ({}) => {
  const organisation = useCurrentOrganisation()
  const isAdmin = useIsOrganisationAdmin()
  if (!organisation) return null
  return (
    <OverflowNav
      gap={3}
      key={organisation.id}
      containerClassName='px-2 pb-1 pb-md-0 pb-mb-0 bg-faint'
      className='py-0 d-flex'
    >
      <NavSubLink
        icon={apps}
        id='projects-link'
        to={Utils.getOrganisationHomePage()}
      >
        Projects
      </NavSubLink>
      <NavSubLink
        data-test='users-and-permissions'
        icon={<UsersIcon />}
        id='permissions-link'
        to={`/organisation/${organisation.id}/permissions`}
      >
        Users and Permissions
      </NavSubLink>
      {!Project.disableAnalytics && isAdmin && (
        <NavSubLink
          icon={statsChart}
          id='permissions-link'
          to={`/organisation/${organisation.id}/usage`}
        >
          Usage
        </NavSubLink>
      )}
      {isAdmin && Utils.getFlagsmithHasFeature('organisation_audit_log') && (
        <NavSubLink
          icon={<AuditLogIcon />}
          id='organisation-audit-log-link'
          to={`/organisation/${organisation.id}/audit-log`}
        >
          Audit Log
        </NavSubLink>
      )}
      {isAdmin && Utils.getFlagsmithHasFeature('organisation_integrations') && (
        <NavSubLink
          icon={<Icon name='layers' />}
          id='integrations-link'
          to={`/organisation/${organisation.id}/integrations`}
        >
          Organisation Integrations
        </NavSubLink>
      )}
      {isAdmin && (
        <NavSubLink
          icon={<Icon name='setting' width={24} />}
          id='org-settings-link'
          data-test='org-settings-link'
          to={`/organisation/${organisation.id}/settings`}
        >
          Organisation Settings
        </NavSubLink>
      )}
    </OverflowNav>
  )
}

export default OrganisationNavbar
