import { IconName } from 'components/Icon'
import SidebarLink from 'components/navigation/SidebarLink'
import { useHistory } from 'react-router-dom'
import React from 'react'

type OrganisationUsageSideBarProps = {
  organisationId: number
  activeTab: 'global' | 'metrics'
}

const OrganisationUsageSideBar = ({
  activeTab,
  organisationId,
}: OrganisationUsageSideBarProps) => {
  const history = useHistory()
  const sideBarItems = [
    {
      icon: 'bar-chart',
      id: 'global',
      label: 'Global Usage',
      to: `/organisation/${organisationId}/usage`,
    },
    {
      icon: 'search',
      id: 'metrics',
      label: 'Metrics',
      to: `/organisation/${organisationId}/usage?p=metrics`,
    },
  ]

  return (
    <div className='d-flex flex-column gap-2 mt-2'>
      {sideBarItems.map((item) => (
        <SidebarLink
          key={item.id}
          id={item.id}
          icon={item.icon as IconName}
          onClick={() => {
            history.push(item.to)
          }}
          active={item.id === activeTab}
          inactiveClassName='fw-bold'
        >
          {item.label}
        </SidebarLink>
      ))}
    </div>
  )
}

export default OrganisationUsageSideBar
