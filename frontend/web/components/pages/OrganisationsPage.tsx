import React, { FC } from 'react'
import ProjectManageWidget from 'components/ProjectManageWidget'
import Button from 'components/base/forms/Button'
import AccountProvider from 'common/providers/AccountProvider'
type OrganisationsPageType = {}

const OrganisationsPage: FC<OrganisationsPageType> = ({}) => {
  return (
    <AccountProvider>
      {({ user }) => {
        return (
          <div className='app-container container'>
            <div className='d-flex justify-content-between'>
              <h5>Organisations</h5>
              <Button>Create New Organisation</Button>
            </div>

            <p className='fs-small lh-sm mb-4'>
              Organisations allow you to manage multiple projects within a team.
            </p>
          </div>
        )
      }}
    </AccountProvider>
  )
}

export default OrganisationsPage
