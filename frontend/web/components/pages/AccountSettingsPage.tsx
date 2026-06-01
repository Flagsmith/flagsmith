import React, { FC, useEffect, useState } from 'react'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
// @ts-ignore
import _data from 'common/data/base/_data'
import ConfigProvider from 'common/providers/ConfigProvider'
import TwoFactor from 'components/TwoFactor'
import Token from 'components/Token'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import JSONReference from 'components/JSONReference'
import { updateAccount } from 'common/services/useAccount'
import { getStore } from 'common/store'
import ChangeEmailAddress from 'components/modals/ChangeEmailAddress'
import ConfirmDeleteAccount from 'components/modals/ConfirmDeleteAccount'
import PageTitle from 'components/PageTitle'
import InfoMessage from 'components/InfoMessage'
import Setting from 'components/Setting'
import AccountStore from 'common/stores/account-store'
import DarkModeSwitch from 'components/DarkModeSwitch'
import SettingTitle from 'components/SettingTitle'
import InputGroup from 'components/base/forms/InputGroup'
import AppActions from 'common/dispatcher/app-actions'
// @ts-ignore
import Project from 'common/project'
import flagsmith from '@flagsmith/flagsmith'
import { Account, AuthType } from 'common/types/responses'

const AccountSettingsPage: FC = () => {
  const [firstName, setFirstName] = useState<string>(
    AccountStore.getUser()?.first_name || '',
  )
  const [lastName, setLastName] = useState<string>(
    AccountStore.getUser()?.last_name || '',
  )
  const [email, setEmail] = useState<string>(
    AccountStore.getUser()?.email || '',
  )
  const [authType, setAuthType] = useState<AuthType | undefined>(
    AccountStore.getUser()?.auth_type,
  )
  const [organisations, setOrganisations] = useState<any[]>(
    AccountStore.getUser()?.organisations || [],
  )
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword1, setNewPassword1] = useState('')
  const [newPassword2, setNewPassword2] = useState('')

  useEffect(() => {
    const handleChange = () => {
      const user = AccountStore.getUser()
      if (user) {
        setFirstName(user.first_name || '')
        setLastName(user.last_name || '')
        setEmail(user.email || '')
        setAuthType(user.auth_type)
        setOrganisations(user.organisations || [])
      }
    }
    AccountStore.on('change', handleChange)
    return () => {
      AccountStore.off('change', handleChange)
    }
  }, [])

  const save = (e: React.FormEvent<HTMLFormElement>) => {
    Utils.preventDefault(e)
    if (isSaving || !firstName || !lastName) {
      return
    }
    setIsSaving(true)
    const account = AccountStore.getUser() as Account
    updateAccount(getStore(), {
      ...account,
      email,
      first_name: firstName,
      last_name: lastName,
    }).then((res: any) => {
      setIsSaving(false)
      if (res.error) {
        setError(
          'There was an error setting your account, please check your details',
        )
      } else {
        toast('Your account has been updated')
      }
    })
  }

  const confirmDeleteAccount = () => {
    openModal(
      'Are you sure?',
      <ConfirmDeleteAccount
        lastUserOrganisations={lastUserOrganisations}
        email={email}
        auth_type={authType}
      />,
      'p-0',
    )
  }

  const invalidateToken = () => {
    openConfirm({
      body: (
        <div>
          Invalidating your token will generate a new token to use with our API,{' '}
          <span className='text-dark font-weight-medium'>
            your current token will no longer work
          </span>
          . Performing this action will also log you out, are you sure you wish
          to do this?
        </div>
      ),
      destructive: true,
      onYes: () => {
        _data.delete(`${Project.api}auth/token/`).then(() => {
          AppActions.logout()
        })
      },
      title: 'Invalidate Token',
      yesText: 'Confirm',
    })
  }

  const savePassword = (e: React.FormEvent<HTMLFormElement>) => {
    Utils.preventDefault(e)
    if (
      !currentPassword ||
      !newPassword1 ||
      !newPassword2 ||
      newPassword2 !== newPassword1
    ) {
      return
    }
    setIsSaving(true)
    _data
      .post(`${Project.api}auth/users/set_password/`, {
        current_password: currentPassword,
        new_password: newPassword1,
        re_new_password: newPassword2,
      })
      .then(() => {
        setIsSaving(false)
        toast('Your password has been updated')
      })
      .catch(() => {
        setIsSaving(false)
        setPasswordError(
          'There was an error setting your password, please check your details.',
        )
      })
  }

  const forced2Factor = AccountStore.forced2Factor()
  const account = AccountStore.getUser() as Account
  const lastUserOrganisations =
    organisations.length >= 1
      ? organisations?.filter((o: any) => o?.num_seats == 1)
      : []

  if (forced2Factor) {
    return (
      <div className='app-container container'>
        <h3>Two-Factor Authentication</h3>
        <p>
          One of your organisations has enfoced Two-Factor Authentication,
          please enable it to continue.
        </p>
        <TwoFactor isLoginPage={true} />
      </div>
    )
  }

  return (
    <div className='app-container container'>
      <PageTitle
        cta={
          <Button
            id='logout-link'
            theme='secondary'
            onClick={AppActions.logout}
          >
            Log Out
          </Button>
        }
        title={'Account Settings'}
      />
      <Tabs uncontrolled className='mt-0'>
        <TabItem tabLabel='General'>
          <div className='mt-4 col-md-8'>
            <SettingTitle>Account Information</SettingTitle>
            <JSONReference
              showNamesButton
              title={'User'}
              json={AccountStore.getUser()}
            />
            <form className='mb-0' onSubmit={save}>
              {!['LDAP', 'SAML'].includes(account?.auth_type) && (
                <div>
                  <InputGroup
                    className='mt-2'
                    title='Email Address'
                    data-test='firstName'
                    inputProps={{
                      className: 'full-width',
                      name: 'groupName',
                      readOnly: true,
                    }}
                    value={email}
                    type='text'
                    name='Email Address'
                  />
                  <div className='text-right'>
                    <Button
                      onClick={() =>
                        openModal(
                          'Change Email Address',
                          <ChangeEmailAddress
                            onComplete={() => {
                              closeModal()
                              AppActions.logout()
                            }}
                          />,
                          'p-0',
                        )
                      }
                      id='change-email-button'
                      data-test='change-email-button'
                      type='button'
                    >
                      Change Email Address
                    </Button>
                  </div>
                </div>
              )}
              <InputGroup
                className='mt-2'
                title='First Name'
                data-test='firstName'
                inputProps={{
                  className: 'full-width',
                  name: 'groupName',
                }}
                value={firstName}
                onChange={(e: any) =>
                  setFirstName(Utils.safeParseEventValue(e))
                }
                isValid={firstName && firstName.length}
                type='text'
                name='First Name*'
              />
              <InputGroup
                className='mb-5'
                title='Last Name'
                data-test='lastName'
                inputProps={{
                  className: 'full-width',
                  name: 'groupName',
                }}
                value={lastName}
                onChange={(e: any) => setLastName(Utils.safeParseEventValue(e))}
                isValid={lastName && lastName.length}
                type='text'
                name='Last Name*'
              />
              {error && <ErrorMessage>{error}</ErrorMessage>}
              <div className='text-right'>
                <Button
                  type='submit'
                  disabled={isSaving || !firstName || !lastName}
                >
                  Save Details
                </Button>
              </div>
            </form>
            <SettingTitle>Appearance</SettingTitle>
            <DarkModeSwitch />
            <SettingTitle>Developer</SettingTitle>
            <Setting
              onChange={(v: boolean) => {
                flagsmith.setTrait('json_inspect', v).then(() => {
                  toast('Updated JSON References setting')
                })
              }}
              checked={!!flagsmith.getTrait('json_inspect')}
              title={'Show JSON References'}
              description={`Enabling this will allow you to inspect the JSON of entities such as features within the platform.`}
            />
            <SettingTitle danger>Delete Account</SettingTitle>
            <Row className='' space>
              <div className='pl-0'>
                <p className='fs-small lh-sm mb-0'>
                  Your account data will be permanently deleted.
                </p>
              </div>
              <Button
                id='delete-user-btn'
                data-test='delete-user-btn'
                onClick={confirmDeleteAccount}
                theme='danger'
              >
                Delete Account
              </Button>
            </Row>
          </div>
        </TabItem>

        <TabItem tabLabel='API Keys'>
          <div className='mt-6'>
            <div className='col-md-6'>
              <h5>Manage API Keys</h5>
              <InfoMessage>
                <p>
                  You can use this token to securely integrate with the private
                  endpoints of our{' '}
                  <Button
                    theme='text'
                    href='https://docs.flagsmith.com/clients/rest#private-api-endpoints'
                    target='_blank'
                    className='fw-normal'
                  >
                    RESTful API
                  </Button>
                  .
                </p>
                <p>
                  This key should <strong>not</strong> be used directly with our
                  SDKs. To configure the Flagsmith SDK, go to the Environment
                  settings page and copy the Environment key from there.
                </p>
              </InfoMessage>
              <p className='fs-small lh-sm'></p>
            </div>
            <div className='col-md-6'>
              <Token className='full-width' token={_data.token} />
              <div className='text-right'>
                <Button
                  onClick={invalidateToken}
                  className='btn btn-danger  mt-5'
                  theme='secondary'
                >
                  Invalidate
                </Button>
              </div>
            </div>
          </div>
        </TabItem>
        <TabItem tabLabel='Security'>
          <div className='mt-4'>
            {account?.auth_type === 'EMAIL' && (
              <div className='col-md-6'>
                <h5 className='mb-5'>Change password</h5>
                <form className='mb-0' onSubmit={savePassword}>
                  <InputGroup
                    title='Current Password'
                    data-test='currentPassword'
                    inputProps={{
                      className: 'full-width',
                      name: 'groupName',
                    }}
                    value={currentPassword}
                    onChange={(e: any) =>
                      setCurrentPassword(Utils.safeParseEventValue(e))
                    }
                    isValid={currentPassword && currentPassword.length}
                    type='password'
                    name='Current Password*'
                    autocomplete='current-password'
                  />
                  <InputGroup
                    className='mt-4'
                    title='New Password'
                    data-test='newPassword'
                    inputProps={{
                      className: 'full-width',
                      name: 'groupName',
                    }}
                    value={newPassword1}
                    onChange={(e: any) =>
                      setNewPassword1(Utils.safeParseEventValue(e))
                    }
                    isValid={newPassword1 && newPassword1.length}
                    type='password'
                    autocomplete='new-password'
                    name='New Password*'
                  />
                  <InputGroup
                    className='mt-4'
                    title='Confirm New Password'
                    data-test='newPassword'
                    inputProps={{
                      className: 'full-width',
                      name: 'groupName',
                    }}
                    value={newPassword2}
                    onChange={(e: any) =>
                      setNewPassword2(Utils.safeParseEventValue(e))
                    }
                    isValid={newPassword2 && newPassword2.length}
                    type='password'
                    autocomplete='new-password'
                    name='Confirm New Password*'
                  />
                  {passwordError && (
                    <ErrorMessage>{passwordError}</ErrorMessage>
                  )}
                  <div className='text-right mt-5'>
                    <Button
                      type='submit'
                      disabled={
                        isSaving ||
                        !newPassword2 ||
                        !newPassword1 ||
                        !currentPassword ||
                        newPassword1 !== newPassword2
                      }
                    >
                      Save Password
                    </Button>
                  </div>
                </form>
              </div>
            )}
            <hr className='py-0 my-4' />
            <div className='col-md-6 col-sm-12'>
              <Setting component={<TwoFactor />} feature='2FA' />
            </div>
          </div>
        </TabItem>
      </Tabs>
    </div>
  )
}

export default ConfigProvider(AccountSettingsPage)
