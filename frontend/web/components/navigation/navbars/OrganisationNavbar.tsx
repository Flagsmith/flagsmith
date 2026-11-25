import React, { FC } from 'react'
import NavSubLink from 'components/navigation/NavSubLink'
import Utils from 'common/utils/utils'
import AccountStore from 'common/stores/account-store'
import Project from 'common/project'
import OverflowNav from 'components/navigation/OverflowNav'
import {
  BarChartIcon,
  GridIcon,
  LayersIcon,
  ListIcon,
  PeopleIcon,
  SettingsIcon,
} from 'components/icons'

type OrganisationNavType = {}

const OrganisationNavbar: FC<OrganisationNavType> = ({}) => {
  return (
    <OverflowNav
      gap={3}
      key={AccountStore.getOrganisation()?.id}
      containerClassName='px-2 pb-1 pb-md-0 pb-mb-0 bg-faint'
      className='py-0 d-flex'
    >
      <NavSubLink
        icon={<GridIcon />}
        id='projects-link'
        to={Utils.getOrganisationHomePage()}
      >
        Projects
      </NavSubLink>
      <NavSubLink
        data-test='users-and-permissions'
        icon={<PeopleIcon />}
        id='permissions-link'
        to={`/organisation/${AccountStore.getOrganisation().id}/permissions`}
      >
        Users and Permissions
      </NavSubLink>
      {!Project.disableAnalytics && AccountStore.isAdmin() && (
        <NavSubLink
          icon={<BarChartIcon />}
          id='permissions-link'
          to={`/organisation/${AccountStore.getOrganisation().id}/usage`}
        >
          Usage
        </NavSubLink>
      )}
      {AccountStore.isAdmin() &&
        Utils.getFlagsmithHasFeature('organisation_audit_log') && (
          <NavSubLink
            icon={<ListIcon />}
            id='organisation-audit-log-link'
            to={`/organisation/${AccountStore.getOrganisation().id}/audit-log`}
          >
            Audit Log
          </NavSubLink>
        )}
      {AccountStore.isAdmin() &&
        Utils.getFlagsmithHasFeature('organisation_integrations') && (
          <NavSubLink
            icon={<LayersIcon />}
            id='integrations-link'
            to={`/organisation/${
              AccountStore.getOrganisation().id
            }/integrations`}
          >
            Organisation Integrations
          </NavSubLink>
        )}
      {AccountStore.isAdmin() && (
        <NavSubLink
          icon={<SettingsIcon />}
          id='org-settings-link'
          data-test='org-settings-link'
          to={`/organisation/${AccountStore.getOrganisation().id}/settings`}
        >
          Organisation Settings
        </NavSubLink>
      )}
    </OverflowNav>
  )
}

export default OrganisationNavbar
