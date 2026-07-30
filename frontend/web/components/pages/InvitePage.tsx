import React, { FC, useEffect, useState } from 'react'
import { useHistory, useParams } from 'react-router-dom'
import AccountProvider from 'common/providers/AccountProvider'
import AppActions from 'common/dispatcher/app-actions'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import API from 'project/api'
import Button from 'components/base/forms/Button'
import Card from 'components/Card'
import Loader from 'components/Loader'

const getErrorMessage = (error: string) => {
  switch (error) {
    case 'No Invite matches the given query.':
    case 'Not found.':
      return 'We could not validate your invite, please check the invite URL and email address you have entered is correct.'
    case 'Please upgrade your plan to add additional seats/users':
      return 'The organisation you have been invited to has no seats available. Please contact the organisation administrator to resolve this before trying again.'
    default:
      return error
  }
}

const InvitePage: FC = () => {
  const { id } = useParams<{ id: string }>()
  const history = useHistory()
  const [isAccepting, setIsAccepting] = useState(false)

  // Carried in the URL rather than in storage, because switching account clears
  // storage on the way out.
  const signInUrl = `/?redirect=${encodeURIComponent(
    document.location.pathname,
  )}`
  const hasSession = !!API.getCookie('t')

  useEffect(() => {
    // Recorded so a session restoring in the background knows an invite is in
    // play. Without it, a user who belongs to no organisation yet gets routed
    // to organisation creation instead of this page. acceptInvite clears it.
    API.setInviteType(
      document.location.pathname.includes('/invite-link/')
        ? 'INVITE_LINK'
        : 'INVITE_EMAIL',
    )
    API.setInvite(id)
    API.trackPage(Constants.pages.INVITE)
  }, [id])

  useEffect(() => {
    if (!hasSession) {
      history.replace(signInUrl)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasSession])

  const onSave = (organisationId: string) => {
    AppActions.selectOrganisation(organisationId)
    history.replace(Utils.getOrganisationHomePage(organisationId))
  }

  return (
    <div className='app-container'>
      <AccountProvider
        onSave={onSave}
        onLogout={() => history.replace(signInUrl)}
      >
        {({ error, user }: { error?: string; user?: { email?: string } }) => {
          if (error) {
            return (
              <div className='centered-container'>
                <div>
                  <h3 className='pt-5'>Oops</h3>
                  <p>{getErrorMessage(error)}</p>
                  <Button onClick={() => history.replace(signInUrl)}>
                    Sign in
                  </Button>
                </div>
              </div>
            )
          }

          // Either the session is still being restored, or we are on our way to
          // sign in, or the invite is being accepted.
          if (!user?.email || isAccepting) {
            return (
              <div className='centered-container'>
                <Loader />
              </div>
            )
          }

          return (
            <div className='centered-container'>
              <Card className='p-4'>
                <h5>Accept your invitation</h5>
                <p className='mb-4'>
                  You are signed in as <strong>{user.email}</strong>. Joining
                  adds this organisation to that account.
                </p>
                <Button
                  data-test='accept-invite-btn'
                  className='full-width'
                  onClick={() => {
                    setIsAccepting(true)
                    AppActions.acceptInvite(id)
                  }}
                >
                  Accept invitation
                </Button>
                <Button
                  theme='text'
                  className='mt-3'
                  onClick={() => AppActions.logout()}
                >
                  Use a different account
                </Button>
              </Card>
            </div>
          )
        }}
      </AccountProvider>
    </div>
  )
}

export default InvitePage
