import React, { FC, useCallback, useEffect, useState } from 'react'
import Constants from 'common/constants'
// eslint-disable-next-line @typescript-eslint/no-var-requires
const _data = require('common/data/base/_data')
import AppActions from 'common/dispatcher/app-actions'
import { useGetProjectQuery } from 'common/services/useProject'
import Icon from 'components/Icon'
import Button from 'components/base/forms/Button'
import InfoMessage from 'components/InfoMessage'
import IdentitySelect from 'components/IdentitySelect'
import FeatureValue from 'components/feature-summary/FeatureValue'
import { removeUserOverride } from 'components/RemoveUserOverride'
import { getPermission } from 'common/services/usePermission'
import { getStore } from 'common/store'
import Project from 'common/project'
import Utils from 'common/utils/utils'
import {
  FeatureState,
  IdentityFeatureState,
  ProjectFlag,
} from 'common/types/responses'
import Switch from 'components/Switch'
import { EnvironmentPermission } from 'common/types/permissions.types'

type IdentityOverride = FeatureState & {
  identity: { id: string; identifier: string }
  segment?: null
  overridden_by?: string | null
}

type Paging = {
  count: number
  currentPage: number
  next: string | null
}

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
  const [userOverrides, setUserOverrides] = useState<IdentityOverride[]>()
  const [userOverridesError, setUserOverridesError] = useState(false)
  const [userOverridesNoPermission, setUserOverridesNoPermission] =
    useState(false)
  const [userOverridesPaging, setUserOverridesPaging] = useState<Paging>({
    count: 0,
    currentPage: 1,
    next: null,
  })
  const [selectedIdentity, setSelectedIdentity] = useState<{
    value: string
    label: string
  } | null>(null)
  const [enabledIdentity, setEnabledIdentity] = useState(false)
  const [_isLoading, setIsLoading] = useState(false)

  const setUserOverridesErrorState = useCallback(() => {
    setUserOverrides([])
    setUserOverridesError(true)
    setUserOverridesNoPermission(false)
    setUserOverridesPaging({ count: 0, currentPage: 1, next: null })
  }, [])

  const setUserOverridesNoPermissionState = useCallback(() => {
    setUserOverrides([])
    setUserOverridesError(false)
    setUserOverridesNoPermission(true)
    setUserOverridesPaging({ count: 0, currentPage: 1, next: null })
  }, [])

  const userOverridesPage = useCallback(
    (page: number, forceRefetch?: boolean) => {
      if (Utils.getIsEdge()) {
        // Early return if tab should be hidden
        if (Utils.getShouldHideIdentityOverridesTab(project)) {
          setUserOverrides([])
          setUserOverridesPaging({ count: 0, currentPage: 1, next: null })
          return
        }

        getPermission(
          getStore(),
          {
            id: environmentId as unknown as number,
            level: 'environment',
          },
          { forceRefetch },
        )
          .then((permissions: Record<string, boolean>) => {
            const hasViewIdentitiesPermission =
              permissions[EnvironmentPermission.VIEW_IDENTITIES] ||
              permissions.ADMIN
            if (!hasViewIdentitiesPermission) {
              setUserOverridesNoPermissionState()
              return
            }

            _data
              .get(
                `${Project.api}environments/${environmentId}/edge-identity-overrides?feature=${projectFlag?.id}&page=${page}`,
              )
              .then(
                (res: {
                  results: Array<{
                    feature_state: FeatureState
                    identity_uuid: string
                    identifier: string
                  }>
                  count: number
                  next: string | null
                }) => {
                  setUserOverrides(
                    res.results.map((v) => ({
                      ...v.feature_state,
                      identity: {
                        id: v.identity_uuid,
                        identifier: v.identifier,
                      },
                    })) as IdentityOverride[],
                  )
                  setUserOverridesError(false)
                  setUserOverridesNoPermission(false)
                  setUserOverridesPaging({
                    count: res.count,
                    currentPage: page,
                    next: res.next,
                  })
                },
              )
              .catch((response: { status?: number }) => {
                if (response?.status === 403) {
                  setUserOverridesNoPermissionState()
                } else {
                  setUserOverridesErrorState()
                }
              })
          })
          .catch(() => {
            setUserOverridesErrorState()
          })
        return
      }

      _data
        .get(
          `${
            Project.api
          }environments/${environmentId}/${Utils.getFeatureStatesEndpoint()}/?anyIdentity=1&feature=${
            projectFlag?.id
          }&page=${page}`,
        )
        .then(
          (res: {
            results: FeatureState[]
            count: number
            next: string | null
          }) => {
            setUserOverrides(res.results as IdentityOverride[])
            setUserOverridesError(false)
            setUserOverridesNoPermission(false)
            setUserOverridesPaging({
              count: res.count,
              currentPage: page,
              next: res.next,
            })
          },
        )
        .catch((response: { status?: number }) => {
          if (response?.status === 403) {
            setUserOverridesNoPermissionState()
          } else {
            setUserOverridesErrorState()
          }
        })
    },
    [
      environmentId,
      project,
      projectFlag?.id,
      setUserOverridesErrorState,
      setUserOverridesNoPermissionState,
    ],
  )

  const changeIdentity = useCallback(
    (items: IdentityOverride[]) => {
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
        userOverridesPage(1)
      })
      setEnabledIdentity(!enabledIdentity)
    },
    [enabledIdentity, environmentId, userOverridesPage],
  )

  const toggleUserFlag = useCallback(
    ({
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
          userOverridesPage(1)
        },
        payload: {
          enabled: !enabled,
          id: identity.id,
          value: identity.identifier,
        },
      })
    },
    [environmentId, userOverridesPage],
  )

  const addItem = useCallback(
    (identity: { value: string; label: string }) => {
      if (!identity?.value) return

      setIsLoading(true)
      _data
        .post(
          `${
            Project.api
          }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${
            identity.value
          }/${Utils.getFeatureStatesEndpoint()}/`,
          {
            enabled: !environmentFlag?.enabled,
            feature: projectFlag?.id,
            feature_state_value: environmentFlag?.feature_state_value || null,
          },
        )
        .then(() => {
          setIsLoading(false)
          setSelectedIdentity(null)
          userOverridesPage(1)
        })
        .catch(() => {
          setIsLoading(false)
          setUserOverridesErrorState()
        })
    },
    [
      environmentId,
      environmentFlag,
      projectFlag?.id,
      setUserOverridesErrorState,
      userOverridesPage,
    ],
  )

  // Load initial data
  useEffect(() => {
    userOverridesPage(1, true)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const renderNoResults = () => {
    if (userOverridesError) {
      return (
        <div className='text-center py-4'>
          Failed to load identity overrides.
        </div>
      )
    }
    if (userOverridesNoPermission) {
      return (
        <div className='text-center py-4'>
          You do not have permission to view identity overrides.
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
            !Utils.getIsEdge() && (
              <Button
                onClick={() => changeIdentity(userOverrides || [])}
                type='button'
                theme='secondary'
                size='small'
              >
                {enabledIdentity ? 'Enable All' : 'Disable All'}
              </Button>
            )
          }
          items={userOverrides}
          paging={userOverridesPaging}
          renderSearchWithNoResults
          nextPage={() =>
            userOverridesPage(userOverridesPaging.currentPage + 1)
          }
          prevPage={() =>
            userOverridesPage(userOverridesPaging.currentPage - 1)
          }
          goToPage={(page: number) => userOverridesPage(page)}
          searchPanel={
            !Utils.getIsEdge() && (
              <div className='text-center mt-2 mb-2'>
                <Flex className='text-left'>
                  <IdentitySelect
                    isEdge={false}
                    ignoreIds={userOverrides?.map((v) => v.identity?.id)}
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
                  <div className='table-column' style={{ width: '65px' }}>
                    <Switch
                      checked={enabled}
                      onChange={() => toggleUserFlag({ enabled, id, identity })}
                      disabled={Utils.getIsEdge()}
                    />
                  </div>
                  <div className='font-weight-medium fs-small lh-sm'>
                    {identity.identifier}
                  </div>
                </Row>
                <Row>
                  <div className='table-column' style={{ width: '188px' }}>
                    {feature_state_value !== null && (
                      <FeatureValue value={feature_state_value} />
                    )}
                  </div>
                  <div className='table-column'>
                    <Button
                      target='_blank'
                      href={`/project/${projectId}/environment/${environmentId}/users/${identity.identifier}/${identity.id}?flag=${projectFlag.name}`}
                      className='btn btn-link fs-small lh-sm font-weight-medium'
                    >
                      <Icon name='edit' width={20} fill='#6837FC' /> Edit
                    </Button>
                    <Button
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation()
                        removeUserOverride({
                          cb: () => userOverridesPage(1, true),
                          environmentId,
                          identifier: identity.identifier,
                          identity: identity.id,
                          identityFlag:
                            identityFlag as unknown as IdentityFeatureState,
                          projectFlag,
                        })
                      }}
                      className='btn ml-2 btn-with-icon'
                    >
                      <Icon name='trash-2' width={20} fill='#656D7B' />
                    </Button>
                  </div>
                </Row>
              </Row>
            )
          }}
          renderNoResults={renderNoResults()}
          isLoading={!userOverrides}
        />
      </FormGroup>
    </>
  )
}

export default IdentityOverridesTab
