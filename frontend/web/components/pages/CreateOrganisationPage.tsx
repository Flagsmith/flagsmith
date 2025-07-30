import React, { useEffect, useRef, useState } from 'react'
import { useHistory } from 'react-router-dom'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import CondensedRow from 'components/CondensedRow'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import API from 'project/api'
import AppActions from 'common/dispatcher/app-actions'
import Utils from 'common/utils/utils'
// @ts-ignore
import Project from 'common/project'
import AccountStore from 'common/stores/account-store'
import { Account } from 'common/types/responses'
import CheckboxGroup from 'components/base/forms/CheckboxGroup'
import OrganisationStore from 'common/stores/organisation-store'

const CreateOrganisationPage: React.FC = () => {
  const [name, setName] = useState<string>('')
  const inputRef = useRef<HTMLInputElement | null>(null)
  const focusTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)
  const history = useHistory()
  const [hosting, setHosting] = useState(['public_saas'])
  const [accountStoreSaving, setAccountStoreSaving] = useState(
    AccountStore.isSaving,
  )

  useEffect(() => {
    const onChangeAccountStore = () => {
      setAccountStoreSaving(AccountStore.isSaving)
    }
    const onSave = () => {
      //@ts-ignore
      const id = AccountStore.savedId
      AppActions.selectOrganisation(id)
      API.setCookie('organisation', `${id}`)

      if (Utils.isSaas()) {
        API.trackTraits({
          hosting_preferences: hosting,
        })
      }

      if (Utils.getFlagsmithHasFeature('welcome_page')) {
        history.push('/getting-started')
      } else {
        history.push(Utils.getOrganisationHomePage(id))
      }
    }
    AccountStore.on('change', onChangeAccountStore)
    AccountStore.on('saved', onSave)
    return () => {
      OrganisationStore.off('change', onChangeAccountStore)
      OrganisationStore.off('saved', onSave)
    }
  }, [hosting, history])

  useEffect(() => {
    API.trackPage(Constants.pages.CREATE_ORGANISATION)
    focusTimeout.current = setTimeout(() => {
      inputRef.current?.focus()
      focusTimeout.current = null
    }, 500)

    return () => {
      if (focusTimeout.current) {
        clearTimeout(focusTimeout.current)
      }
    }
  }, [])

  if (
    Project.superUserCreateOnly &&
    // @ts-ignore
    !(AccountStore.model as Account)?.is_superuser
  ) {
    return (
      <div className='text-center alert'>
        Your Flagsmith instance is setup to only allow super users to create an
        organisation, please contact your administrator.
      </div>
    )
  }

  if (Utils.getFlagsmithHasFeature('disable_create_org')) {
    return (
      <div id='create-org-page' className='container app-container'>
        This Flagsmith instance is configured to prevent additional
        organisations from being created. Please contact an administrator. If
        you think you are seeing this page by mistake, please check you are
        invited to the correct organisation.
      </div>
    )
  }

  return (
    <div id='create-org-page' className='container app-container'>
      <PageTitle title='Create your organisation'>
        Organisations allow you to manage multiple projects within a team.
      </PageTitle>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (Project.capterraKey) {
            const parts = Project.capterraKey.split(',')
            Utils.appendImage(
              `https://ct.capterra.com/capterra_tracker.gif?vid=${parts[0]}&vkey=${parts[1]}`,
            )
          }
          AppActions.createOrganisation(name)
        }}
      >
        <CondensedRow>
          <InputGroup
            ref={inputRef as any}
            inputProps={{ className: 'full-width', name: 'orgName' }}
            title='Organisation Name'
            placeholder='E.g. ACME Ltd'
            onChange={(e: InputEvent) => setName(Utils.safeParseEventValue(e))}
          />
          {Utils.isSaas() && (
            <InputGroup
              inputProps={{ className: 'full-width', name: 'orgName' }}
              title={
                <div>
                  What is your company's desired hosting option?{' '}
                  <a
                    className='text-primary'
                    href='https://docs.flagsmith.com/version-comparison'
                    target='_blank'
                    rel='noreferrer'
                  >
                    View Docs
                  </a>
                </div>
              }
              component={
                <CheckboxGroup
                  onChange={setHosting}
                  selectedValues={hosting}
                  items={[
                    {
                      label: 'Public SaaS (Multi Tenant)',
                      value: 'public_saas',
                    },
                    {
                      label: 'Private SaaS (Single Tenant)',
                      value: 'private_saas',
                    },
                    {
                      label: 'Self Hosted (in your own cloud)',
                      value: 'self_hosted',
                    },
                  ]}
                />
              }
            />
          )}

          <div className='text-right'>
            <Button
              type='submit'
              disabled={accountStoreSaving || !name}
              id='create-org-btn'
            >
              Create Organisation
            </Button>
          </div>
        </CondensedRow>
      </form>
    </div>
  )
}

export default ConfigProvider(CreateOrganisationPage)
