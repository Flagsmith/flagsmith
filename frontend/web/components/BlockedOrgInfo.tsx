import React from 'react'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import Link from './base/link'

export default function BlockedOrgInfo() {
  return (
    <div className='text-nowrap'>
      <div>Organisation name: {AccountStore.getOrganisation().name}</div>
      <div>Organisation ID: {AccountStore.getOrganisation().id}</div>
      <div>
        <Link to={`/organisation/${AccountStore.getOrganisation().id}/usage`}>
          See your usage
        </Link>
      </div>
      <div>
        <Link to='/organisations'>Switch to a different organisation</Link>
      </div>
      <div>
        <Link
          href='/login'
          onClick={() => {
            AppActions.logout()
          }}
        >
          Log out
        </Link>
      </div>
    </div>
  )
}
