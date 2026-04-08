import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import AppActions from 'common/dispatcher/app-actions'
import FeatureListStore from 'common/stores/feature-list-store'
import { useGetProjectQuery } from 'common/services/useProject'
import Icon from 'components/Icon'
import Button from 'components/base/forms/Button'
import InfoMessage from 'components/InfoMessage'
import IdentitySelect from 'components/IdentitySelect'
import FeatureValue from 'components/feature-summary/FeatureValue'
import { removeUserOverride } from 'components/RemoveUserOverride'
import { useHasPermission } from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import {
  FeatureState,
  IdentityFeatureState,
  IdentityOverride,
  ProjectFlag,
} from 'common/types/responses'
import Switch from 'components/Switch'
import { EnvironmentPermission } from 'common/types/permissions.types'
import {
  useCreateIdentityOverrideMutation,
  useGetIdentityOverridesQuery,
} from 'common/services/useIdentityOverride'

type IdentityOverridesTabProps = {
  environmentId: string
  projectId: number
  projectFlag: ProjectFlag
  environmentFlag?: FeatureState
}

const IdentityOverridesTab: FC<IdentityOverridesTabProps> = ({
  environmentFlag,
  environmentId,
  projectFlag,
  projectId,
}) => {
  const { data: project } = useGetProjectQuery({ id: projectId })
  const [page, setPage] = useState(1)
  const [selectedIdentity, setSelectedIdentity] = useState<{
    value: string
    label: string
  } | null>(null)
  const [enabledIdentity, setEnabledIdentity] = useState(false)

  const isEdge = Utils.getIsEdge()
  const shouldHideTab = Utils.getShouldHideIdentityOverridesTab(project)

  const {
    isLoading: isPermissionLoading,
    permission: hasViewIdentitiesPermission,
  } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: EnvironmentPermission.VIEW_IDENTITIES,
  })

  const skipFetch =
    shouldHideTab ||
    (isEdge && (isPermissionLoading || !hasViewIdentitiesPermission))

  const { data, isError, isLoading, refetch } = useGetIdentityOverridesQuery(
    { environmentId, featureId: projectFlag.id, isEdge, page },
    { skip: skipFetch },
  )

  const [createIdentityOverride] = useCreateIdentityOverrideMutation()

  const addItem = (identity: { value: string; label: string }) => {
    if (!identity?.value) return
    createIdentityOverride({
      enabled: !environmentFlag?.enabled,
      environmentId,
      featureId: projectFlag.id,
      feature_state_value: environmentFlag?.feature_state_value ?? null,
      identityId: identity.value,
    }).then(() => {
      setSelectedIdentity(null)
      refetch()
      FeatureListStore.trigger('saved', {})
    })
  }

  const changeIdentity = (items: IdentityOverride[]) => {
    Promise.all(
      items.map(
        (item) =>
          new Promise<void>((resolve) => {
            AppActions.changeUserFlag({
              environmentId,
              identity: item.identity.id,
              identityFlag: item.id,
              onSuccess: resolve,
              payload: {
                enabled: enabledIdentity,
                id: item.identity.id,
                value: item.identity.identifier,
              },
            })
          }),
      ),
    ).then(() => {
      refetch()
    })
    setEnabledIdentity(!enabledIdentity)
  }

  const toggleUserFlag = ({
    enabled,
    id,
    identity,
  }: {
    enabled: boolean
    id: number
    identity: { id: string; identifier: string }
  }) => {
    AppActions.changeUserFlag({
      environmentId,
      identity: identity.id,
      identityFlag: id,
      onSuccess: () => {
        refetch()
      },
      payload: {
        enabled: !enabled,
        id: identity.id,
        value: identity.identifier,
      },
    })
  }

  const renderNoResults = () => {
    if (isEdge && !isPermissionLoading && !hasViewIdentitiesPermission) {
      return (
        <div className='text-center py-4'>
          You do not have permission to view identity overrides.
        </div>
      )
    }
    if (isError) {
      return (
        <div className='text-center py-4'>
          Failed to load identity overrides.
        </div>
      )
    }
    return (
      <Row className='list-item'>
        <div className='table-column'>
          No identities are overriding this feature.
        </div>
      </Row>
    )
  }

  return (
    <>
      <FormGroup className='mb-4 mt-2'>
        <PanelSearch
          id='users-list'
          className='no-pad identity-overrides-title'
          title={
            <>
              <Tooltip
                title={
                  <h5 className='mb-0'>
                    Identity Overrides{' '}
                    <Icon name='info-outlined' width={20} fill='#9DA4AE' />
                  </h5>
                }
                place='top'
              >
                {Constants.strings.IDENTITY_OVERRIDES_DESCRIPTION}
              </Tooltip>
              <div className='fw-normal transform-none mt-4'>
                <InfoMessage collapseId='identity-overrides'>
                  Identity overrides override feature values for individual
                  identities. The overrides take priority over an segment
                  overrides and environment defaults. Identity overrides will
                  only apply when you identify via the SDK.{' '}
                  <a
                    target='_blank'
                    href='https://docs.flagsmith.com/basic-features/managing-identities'
                    rel='noreferrer'
                  >
                    Check the Docs for more details
                  </a>
                  .
                </InfoMessage>
              </div>
            </>
          }
          action={
            !isEdge && (
              <Button
                onClick={() => changeIdentity(data?.results || [])}
                type='button'
                theme='secondary'
                size='small'
              >
                {enabledIdentity ? 'Enable All' : 'Disable All'}
              </Button>
            )
          }
          items={data?.results}
          paging={{ ...data, currentPage: page }}
          renderSearchWithNoResults
          nextPage={() => setPage((p) => p + 1)}
          prevPage={() => setPage((p) => p - 1)}
          goToPage={setPage}
          searchPanel={
            !isEdge && (
              <div className='text-center mt-2 mb-2'>
                <Flex className='text-left'>
                  <IdentitySelect
                    isEdge={false}
                    ignoreIds={data?.results?.map((v) => v.identity?.id)}
                    environmentId={environmentId}
                    data-test='select-identity'
                    placeholder='Create an Identity Override...'
                    value={selectedIdentity}
                    onChange={(identity: { value: string; label: string }) => {
                      setSelectedIdentity(identity)
                      addItem(identity)
                    }}
                  />
                </Flex>
              </div>
            )
          }
          renderRow={(identityFlag: IdentityOverride) => {
            const { enabled, feature_state_value, id, identity } = identityFlag
            return (
              <Row space className='list-item cursor-pointer' key={id}>
                <Row>
                  <div className='font-weight-medium fs-small lh-sm ms-3'>
                    {identity.identifier}
                  </div>
                </Row>
                <Row>
                  <div className='table-column' style={{ width: '188px' }}>
                    {feature_state_value !== null && (
                      <FeatureValue value={feature_state_value} />
                    )}
                  </div>
                  <div className='table-column' style={{ width: '65px' }}>
                    <Switch
                      checked={enabled}
                      onChange={() => toggleUserFlag({ enabled, id, identity })}
                      disabled={isEdge}
                    />
                  </div>
                  <div className='table-column d-flex align-items-center'>
                    <Button
                      target='_blank'
                      href={`/project/${projectId}/environment/${environmentId}/identities/${identity.identifier}/${identity.id}?flag=${projectFlag.name}`}
                      className='btn btn-link fs-small lh-sm font-weight-medium me-4'
                    >
                      <Icon name='edit' width={20} fill='#6837FC' /> Edit
                    </Button>
                    <Button
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation()
                        removeUserOverride({
                          cb: () => {
                            refetch()
                            FeatureListStore.trigger('saved', {})
                          },
                          environmentId,
                          identifier: identity.identifier,
                          identity: identity.id,
                          identityFlag:
                            identityFlag as unknown as IdentityFeatureState,
                          projectFlag,
                        })
                      }}
                      className='btn btn-with-icon'
                    >
                      <Icon name='trash-2' width={20} fill='#656D7B' />
                    </Button>
                  </div>
                </Row>
              </Row>
            )
          }}
          renderNoResults={renderNoResults()}
          isLoading={isLoading || isPermissionLoading}
        />
      </FormGroup>
    </>
  )
}

export default IdentityOverridesTab
