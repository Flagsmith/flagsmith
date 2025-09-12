import React, { FC } from 'react'
import PanelSearch from './PanelSearch'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import Button from './base/forms/Button'
import FeatureValue from './feature-summary/FeatureValue'
import Icon from './Icon'
import Panel from './base/grid/Panel'
import { useHasPermission } from 'common/providers/Permission'
import API from 'project/api'
import CreateTraitModal from './modals/CreateTrait'
import {
  useDeleteIdentityTraitMutation,
  useGetIdentityTraitsQuery,
} from 'common/services/useIdentityTrait'
import { IdentityTrait } from 'common/types/responses'

type IdentityTraitsType = {
  projectId: string
  environmentId: string
  identityName: string
  identityId: string
}

const IdentityTraits: FC<IdentityTraitsType> = ({
  environmentId,
  identityId,
  identityName,
  projectId,
}) => {
  const use_edge_identities = Utils.getIsEdge()

  const { permission: manageUserPermission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: Utils.getManageUserPermission(),
  })

  const { data: traits } = useGetIdentityTraitsQuery({
    environmentId,
    identity: identityId,
    use_edge_identities,
  })

  const [deleteTrait, { isLoading: deletingTrait }] =
    useDeleteIdentityTraitMutation({})

  const onTraitSaved = () => {
    closeModal?.()
  }

  const createTrait = () => {
    API.trackEvent(Constants.events.VIEW_USER_FEATURE)
    openModal(
      'Create User Trait',
      <CreateTraitModal
        isEdit={false}
        onSave={onTraitSaved}
        identity={identityId}
        identityName={decodeURIComponent(identityName)}
        environmentId={environmentId}
        projectId={projectId}
      />,
      'p-0',
    )
  }

  const editTrait = (trait: IdentityTrait) => {
    openModal(
      'Edit User Trait',
      <CreateTraitModal
        isEdit
        {...trait}
        onSave={onTraitSaved}
        identity={identityId}
        identityName={decodeURIComponent(identityName)}
        environmentId={environmentId}
        projectId={projectId}
      />,
      'p-0',
    )
  }

  const removeTrait = (traitId: string, trait_key: string) => {
    openConfirm({
      body: (
        <div>
          {'Are you sure you want to delete trait '}
          <strong>{trait_key}</strong>
          {
            ' from this user? Traits can be re-added here or via one of our SDKs.'
          }
        </div>
      ),
      destructive: true,
      onYes: () =>
        deleteTrait({
          data: {
            id: traitId,
            trait_key: trait_key,
          },
          environmentId,
          identity: identityId,
          use_edge_identities,
        }).then((res) => {
          // @ts-ignore
          if (!res?.error) {
            onTraitSaved()
          }
        }),
      title: 'Delete Trait',
      yesText: 'Confirm',
    })
  }

  return (
    <FormGroup>
      <PanelSearch
        id='user-traits-list'
        className='no-pad'
        itemHeight={65}
        title='Traits'
        items={traits}
        actionButton={
          <div className='ml-2'>
            {Utils.renderWithPermission(
              manageUserPermission,
              Constants.environmentPermissions(
                Utils.getManageUserPermissionDescription(),
              ),
              <Button
                disabled={!manageUserPermission}
                id='add-trait'
                data-test='add-trait'
                onClick={createTrait}
                size='small'
              >
                Add new trait
              </Button>,
            )}
          </div>
        }
        header={
          <Row className='table-header'>
            <Flex className='table-column px-3'>Trait</Flex>
            <Flex className='table-column'>Value</Flex>
            <div className='table-column' style={{ width: '80px' }}>
              Remove
            </div>
          </Row>
        }
        renderRow={({ id, trait_key, trait_value }: any, i: number) => (
          <Row
            className='list-item clickable'
            key={trait_key}
            space
            data-test={`user-trait-${i}`}
            onClick={() =>
              editTrait({
                id,
                trait_key,
                trait_value,
              })
            }
          >
            <Flex className='table-column px-3'>
              <div className={`js-trait-key-${i} font-weight-medium`}>
                {trait_key}
              </div>
            </Flex>
            <Flex className='table-column'>
              <FeatureValue
                includeEmpty
                data-test={`user-trait-value-${i}`}
                value={trait_value}
              />
            </Flex>
            <div
              className='table-column text-center'
              style={{ width: '80px' }}
              onClick={(e) => e.stopPropagation()}
            >
              {Utils.renderWithPermission(
                manageUserPermission,
                Constants.environmentPermissions(
                  Utils.getManageUserPermissionDescription(),
                ),
                <Button
                  id='remove-feature'
                  className='btn btn-with-icon'
                  type='button'
                  disabled={!manageUserPermission}
                  onClick={() => removeTrait(id, trait_key)}
                  data-test={`delete-user-trait-${i}`}
                >
                  <Icon name='trash-2' width={20} fill='#656D7B' />
                </Button>,
              )}
            </div>
          </Row>
        )}
        renderNoResults={
          <Panel
            title='Traits'
            className='no-pad'
            action={
              <div>
                {Utils.renderWithPermission(
                  manageUserPermission,
                  Constants.environmentPermissions(
                    Utils.getManageUserPermissionDescription(),
                  ),
                  <Button
                    disabled={!manageUserPermission}
                    className='mb-2'
                    id='add-trait'
                    data-test='add-trait'
                    onClick={createTrait}
                    size='small'
                  >
                    Add new trait
                  </Button>,
                )}
              </div>
            }
          >
            <div className='search-list'>
              <Row className='list-item text-muted px-3'>
                This user has no traits.
              </Row>
            </div>
          </Panel>
        }
        filterRow={({ trait_key }: any, searchString: string) =>
          trait_key.toLowerCase().indexOf(searchString.toLowerCase()) > -1
        }
      />
    </FormGroup>
  )
}

export default IdentityTraits
