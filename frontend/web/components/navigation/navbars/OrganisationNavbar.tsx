import React, { FC } from 'react'
import NavSubLink from 'components/navigation/NavSubLink'
import { apps, statsChart } from 'ionicons/icons'
import Utils from 'common/utils/utils'
import UsersIcon from 'components/svg/UsersIcon'
import AccountStore from 'common/stores/account-store'
import Project from 'common/project'
import Icon from 'components/Icon'
import OverflowNav from 'components/navigation/OverflowNav'

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
        to={`/organisation/${AccountStore.getOrganisation().id}/permissions`}
      >
        Users and Permissions
      </NavSubLink>
      {!Project.disableAnalytics && AccountStore.isAdmin() && (
        <NavSubLink
          icon={statsChart}
          id='permissions-link'
          to={`/organisation/${AccountStore.getOrganisation().id}/usage`}
        >
          Usage
        </NavSubLink>
      )}
      {AccountStore.isAdmin() && (
        <>
          {Utils.getFlagsmithHasFeature('organisation_integrations') && (
            <NavSubLink
              icon={<Icon name='layers' />}
              id='integrations-link'
              to={`/organisation/${
                AccountStore.getOrganisation().id
              }/integrations`}
            >
              Organisation Integrations
            </NavSubLink>
          )}
          <NavSubLink
            icon={<Icon name='setting' width={24} />}
            id='org-settings-link'
            data-test='org-settings-link'
            to={`/organisation/${AccountStore.getOrganisation().id}/settings`}
          >
            Organisation Settings
          </NavSubLink>
        </>
      )}
    </OverflowNav>
  )
}

export default OrganisationNavbar
