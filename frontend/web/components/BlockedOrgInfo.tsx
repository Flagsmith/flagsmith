import React from 'react'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'

export default function BlockedOrgInfo() {
  return (
    <div className='text-nowrap'>
      <div>Organization name: {AccountStore.getOrganisation().name}</div>
      <div>Organization ID: {AccountStore.getOrganisation().id}</div>
      <div>
        <a href='/organisations'>Switch to a different organization</a>
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
