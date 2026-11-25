import { BarChartIcon, SearchIcon } from 'components/icons'
import SidebarLink from 'components/navigation/SidebarLink'
import { useHistory } from 'react-router-dom'
import React from 'react'

type OrganisationUsageSideBarProps = {
  organisationId: number
  activeTab: 'global' | 'user-agents'
}

const OrganisationUsageSideBar = ({
  activeTab,
  organisationId,
}: OrganisationUsageSideBarProps) => {
  const history = useHistory()
  const sideBarItems = [
    {
      icon: BarChartIcon,
      id: 'global',
      label: 'By Endpoint',
      to: `/organisation/${organisationId}/usage`,
    },
    {
      icon: SearchIcon,
      id: 'user-agents',
      label: 'By SDK',
      to: `/organisation/${organisationId}/usage?p=user-agents`,
    },
  ]

  return (
    <div className='d-flex flex-column gap-2 mt-2'>
      {sideBarItems.map((item) => (
        <SidebarLink
          key={item.id}
          id={item.id}
          icon={item.icon}
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
