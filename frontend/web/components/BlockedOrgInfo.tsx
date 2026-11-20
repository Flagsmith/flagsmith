import React from 'react'
import { useCurrentOrganisation } from 'common/hooks/useCurrentOrganisation'
import AppActions from 'common/dispatcher/app-actions'

export default function BlockedOrgInfo() {
  const organisation = useCurrentOrganisation()
  if (!organisation) return null
  return (
    <div className='text-nowrap'>
      <div>Organisation name: {organisation.name}</div>
      <div>Organisation ID: {organisation.id}</div>
      <div>
        <a href={`/organisation/${organisation.id}/usage`}>See your usage</a>
      </div>
      <div>
        <a href='/organisations'>Switch to a different organisation</a>
      </div>
      <div>
        <a
          href='/login'
          onClick={() => {
            AppActions.logout()
          }}
        >
          Log out
        </a>
      </div>
    </div>
  )
}
