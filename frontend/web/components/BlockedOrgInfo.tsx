import React from 'react'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'

export default function BlockedOrgInfo() {
  return (
    <div className='text-nowrap'>
      <div>Organisation name: {AccountStore.getOrganisation().name}</div>
      <div>Organisation ID: {AccountStore.getOrganisation().id}</div>
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
