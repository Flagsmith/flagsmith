import React, { FC } from 'react'
import {
  HealthProvider,
  Role,
  User,
  UserGroupSummary,
  UserPermission,
} from 'common/types/responses'
import PanelSearch from './PanelSearch'
import Button from './base/forms/Button'

import { PermissionLevel, Req } from 'common/types/requests'
import { RouterChildContext } from 'react-router'

import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from './Icon'

import Utils from 'common/utils/utils'
import {
  useCreateHealthProviderMutation,
  useGetHealthProvidersQuery,
} from 'common/services/useHealthProvider'
import { components } from 'react-select'

type EditPermissionModalType = {
  group?: UserGroupSummary
  projectId: number
  className?: string
  isGroup?: boolean
  level: PermissionLevel
  name: string
  onSave?: () => void
  envId?: number | string | undefined
  parentId?: string
  parentLevel?: string
  parentSettingsLink?: string
  roleTabTitle?: string
  permissions?: UserPermission[]
  push: (route: string) => void
  user?: User
  role?: Role
  roles?: Role[]
  permissionChanged?: () => void
  isEditUserPermission?: boolean
  isEditGroupPermission?: boolean
}

type EditHealthProviderType = Omit<EditPermissionModalType, 'onSave'> & {
  router: RouterChildContext['router']
  tabClassName?: string
}

const CreateHealthProviderForm = ({ projectId }: { projectId: number }) => {
  const [selected, setSelected] = React.useState<string | undefined>()
  const [createProvider, { isError, isLoading, isSuccess }] =
    useCreateHealthProviderMutation()

  const providers = [{ name: 'Sample' }, { name: 'Grafana' }]

  const providerOptions = providers.map((provider) => ({
    label: provider.name,
    value: provider.name,
  }))

  return (
    <form
      className='col-md-8'
      onSubmit={(e) => {
        e.preventDefault()
        if (!selected) {
          return
        }
        createProvider({ name: selected, projectId })
      }}
    >
      <Row className='align-items-start'>
        <Flex className='ml-0'>
          <Select
            disabled={!providerOptions?.length}
            placeholder='Select a provider'
            data-test='add-health-provider-select'
            components={{
              Option: (props: any) => {
                return (
                  <components.Option {...props}>
                    {props.children}
                  </components.Option>
                )
              },
            }}
            value={providerOptions.find((v) => v.value === selected)}
            onChange={(option: { value: string }) => {
              setSelected(option.value)
            }}
            options={providerOptions}
          />
        </Flex>
      </Row>
      <div className='text-right mt-4'>
        <Button
          type='submit'
          id='save-proj-btn'
          disabled={isLoading || !selected}
          className='ml-3'
        >
          {isLoading ? 'Creating' : 'Create'}
        </Button>
      </div>
    </form>
  )
}

const EditHealthProvider: FC<EditHealthProviderType> = ({
  envId,
  level,
  permissions,
  projectId,
  roleTabTitle,
  roles,
  router,
  tabClassName,
}) => {
  const { data: healthProviders, isLoading } = useGetHealthProvidersQuery({
    projectId,
  })

  return (
    <div className='mt-4'>
      <Row>
        <h5>Create Health Providers</h5>
      </Row>
      <p className='fs-small lh-sm col-md-8 mb-4'>
        Flagsmith lets you connect health providers for tagging feature flags
        unhealthy state in different environments.{' '}
        <Button
          theme='text'
          href='' // TODO: Add docs
          target='_blank'
          className='fw-normal'
        >
          Learn about Feature Health.
        </Button>
      </p>

      <label>Provider Name</label>
      <CreateHealthProviderForm projectId={projectId} />
      <hr className='py-0 my-4' />

      <div className='mt-4'>
        {isLoading && (
          <div className='centered-container'>
            <Loader />
          </div>
        )}
        {!isLoading && !!healthProviders?.length && (
          <div className={tabClassName}>
            <PanelSearch
              id='project-health-providers-list'
              title='Health Providers'
              className='panel--transparent'
              items={healthProviders}
              itemHeight={64}
              header={
                <Row className='table-header'>
                  <Flex className='table-column px-3'>Provider</Flex>
                  <Flex className='table-column'>Webhook URL</Flex>
                </Row>
              }
              renderRow={(provider: HealthProvider) => {
                const { name, webhook_url: webhook } = provider
                const matchingPermissions = {
                  admin: true,
                }

                return (
                  <Row
                    space
                    className={`list-item${
                      matchingPermissions?.admin ? '' : ' clickable'
                    }`}
                    key={projectId}
                  >
                    <Flex className='table-column px-3'>
                      <div className='mb-1 font-weight-medium'>{name}</div>
                    </Flex>
                    {matchingPermissions?.admin && (
                      <Flex className='table-column fs-small lh-sm'>
                        <div className='d-flex align-items-center'>
                          <div
                            style={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              width: '280px',
                            }}
                          >
                            {webhook}
                          </div>
                          <Button
                            onClick={() => {
                              Utils.copyFeatureName(webhook)
                            }}
                            theme='icon'
                            className='ms-2'
                          >
                            <Icon name='copy' />
                          </Button>
                        </div>
                      </Flex>
                    )}
                    <div style={{ width: '80px' }} className='text-center'>
                      {matchingPermissions?.admin && (
                        <Icon name='setting' width={20} fill='#656D7B' />
                      )}
                    </div>
                  </Row>
                )
              }}
              renderNoResults={
                <div>You have no health provider in this project.</div>
              }
              filterRow={(item: HealthProvider, search: string) => {
                const strToSearch = `${item.name} ${item.webhook_url}`
                return (
                  strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1
                )
              }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default ConfigProvider(EditHealthProvider) as unknown as FC<
  Omit<EditHealthProviderType, 'router'>
>
