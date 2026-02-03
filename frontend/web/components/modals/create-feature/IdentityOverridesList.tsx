import React, { FC } from 'react'
import PanelSearch from 'components/PanelSearch'
import InfoMessage from 'components/InfoMessage'
import Constants from 'common/constants'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import IdentitySelect from 'components/IdentitySelect'
import FeatureValue from 'components/feature-summary/FeatureValue'
import Utils from 'common/utils/utils'
import { FeatureState, ProjectFlag } from 'common/types/responses'

type UserOverrideType = FeatureState & {
  identity: { id: string; identifier: string }
}

type SelectedIdentity = { value: string; label?: string }

type IdentityOverridesListProps = {
  userOverrides?: UserOverrideType[]
  userOverridesError: boolean
  userOverridesNoPermission: boolean
  userOverridesPaging?: {
    count: number
    currentPage: number
    next: string | null
  }
  enabledIndentity: boolean
  selectedIdentity: SelectedIdentity | null
  environmentId: string
  projectId: number
  projectFlag: ProjectFlag
  onChangeIdentity: (items: UserOverrideType[]) => void
  onToggleUserFlag: (params: {
    enabled: boolean
    id: number
    identity: { id: string; identifier: string }
  }) => void
  onUserOverridesPage: (page: number) => void
  onSelectedIdentityChange: (identity: SelectedIdentity | null) => void
  onAddItem: () => void
  onRemoveUserOverride: (params: {
    cb: () => void
    environmentId: string
    identifier: string
    identity: string
    identityFlag: UserOverrideType
    projectFlag: ProjectFlag
  }) => void
}

const IdentityOverridesList: FC<IdentityOverridesListProps> = ({
  enabledIndentity,
  environmentId,
  onAddItem,
  onChangeIdentity,
  onRemoveUserOverride,
  onSelectedIdentityChange,
  onToggleUserFlag,
  onUserOverridesPage,
  projectFlag,
  projectId,
  selectedIdentity,
  userOverrides,
  userOverridesError,
  userOverridesNoPermission,
  userOverridesPaging,
}) => {
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
            <InfoMessage collapseId={'identity-overrides'}>
              Identity overrides override feature values for individual
              identities. The overrides take priority over an segment overrides
              and environment defaults. Identity overrides will only apply when
              you identify via the SDK.{' '}
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
            onClick={() => onChangeIdentity(userOverrides || [])}
            type='button'
            theme='secondary'
            size='small'
          >
            {enabledIndentity ? 'Enable All' : 'Disable All'}
          </Button>
        )
      }
      items={userOverrides}
      paging={userOverridesPaging}
      renderSearchWithNoResults
      nextPage={() =>
        onUserOverridesPage((userOverridesPaging?.currentPage || 0) + 1)
      }
      prevPage={() =>
        onUserOverridesPage((userOverridesPaging?.currentPage || 2) - 1)
      }
      goToPage={(page: number) => onUserOverridesPage(page)}
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
                onChange={(si: SelectedIdentity) => {
                  onSelectedIdentityChange(si)
                  setTimeout(() => onAddItem(), 0)
                }}
              />
            </Flex>
          </div>
        )
      }
      renderRow={(identityFlag: UserOverrideType) => {
        const {
          enabled,
          feature_state_value,
          id,
          identity: flagIdentity,
        } = identityFlag
        return (
          <Row space className='list-item cursor-pointer' key={id}>
            <Row>
              <div
                className='table-column'
                style={{
                  width: '65px',
                }}
              >
                <Switch
                  checked={enabled}
                  onChange={() =>
                    onToggleUserFlag({
                      enabled,
                      id,
                      identity: flagIdentity,
                    })
                  }
                  disabled={Utils.getIsEdge()}
                />
              </div>
              <div className='font-weight-medium fs-small lh-sm'>
                {flagIdentity.identifier}
              </div>
            </Row>
            <Row>
              <div
                className='table-column'
                style={{
                  width: '188px',
                }}
              >
                {feature_state_value !== null && (
                  <FeatureValue value={feature_state_value} />
                )}
              </div>
              <div className='table-column'>
                <Button
                  target='_blank'
                  href={`/project/${projectId}/environment/${environmentId}/users/${flagIdentity.identifier}/${flagIdentity.id}?flag=${projectFlag.name}`}
                  className='btn btn-link fs-small lh-sm font-weight-medium'
                >
                  <Icon name='edit' width={20} fill='#6837FC' /> Edit
                </Button>
                <Button
                  onClick={(e: React.MouseEvent) => {
                    e.stopPropagation()
                    onRemoveUserOverride({
                      cb: () => onUserOverridesPage(1),
                      environmentId,
                      identifier: flagIdentity.identifier,
                      identity: flagIdentity.id,
                      identityFlag,
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
  )
}

export default IdentityOverridesList
