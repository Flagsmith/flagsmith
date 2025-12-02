import React, { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import Constants from 'common/constants'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import AddEditTags from 'components/tags/AddEditTags'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import Permission from 'common/providers/Permission'
import FlagOwners from 'components/FlagOwners'
import FlagOwnerGroups from 'components/FlagOwnerGroups'
import PlanBasedBanner from 'components/PlanBasedAccess'
import Switch from 'components/Switch'
import Tooltip from 'components/Tooltip'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'
import FormGroup from 'components/base/grid/FormGroup'
import Row from 'components/base/grid/Row'
import AccountStore from 'common/stores/account-store'
type FeatureSettingsTabProps = {
  projectAdmin: boolean
  createFeature: boolean
  featureContentType: any
  identity?: string
  isEdit: boolean
  projectId: number | string
  projectFlag: ProjectFlag | null
  onChange: (projectFlag: ProjectFlag) => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
}

const FeatureSettings: FC<FeatureSettingsTabProps> = ({
  createFeature,
  featureContentType,
  identity,
  isEdit,
  onChange,
  onHasMetadataRequiredChange,
  projectFlag,
  projectId,
}) => {
  const metadataEnable = Utils.getPlansPermission('METADATA')

  if (!createFeature) {
    return (
      <InfoMessage>
        <div
          dangerouslySetInnerHTML={{
            __html: Constants.projectPermissions('Create Feature'),
          }}
        />
      </InfoMessage>
    )
  }

  if (!projectFlag) {
    return null
  }
  return (
    <>
      {!identity && projectFlag?.tags && (
        <FormGroup className='mb-3 setting'>
          <InputGroup
            title={'Tags'}
            tooltip={Constants.strings.TAGS_DESCRIPTION}
            component={
              <AddEditTags
                readOnly={!!identity || !createFeature}
                projectId={`${projectId}`}
                value={projectFlag.tags}
                onChange={(tags) => onChange({ ...projectFlag, tags })}
              />
            }
          />
        </FormGroup>
      )}
      {metadataEnable && featureContentType?.id && (
        <>
          <label className='mt-1'>Custom Fields</label>
          <AddMetadataToEntity
            organisationId={AccountStore.getOrganisation().id}
            projectId={projectId}
            entityId={projectFlag?.id}
            entityContentType={featureContentType?.id}
            entity={featureContentType?.model}
            setHasMetadataRequired={onHasMetadataRequiredChange}
            onChange={(metadata) => onChange({ ...projectFlag, metadata })}
          />
        </>
      )}
      {!identity && projectFlag?.id && (
        <Permission level='project' permission='CREATE_FEATURE' id={projectId}>
          {({ permission }) =>
            permission && (
              <>
                <FormGroup className='mb-3 setting'>
                  <FlagOwners projectId={projectId} id={projectFlag.id} />
                </FormGroup>
                <FormGroup className='mb-3 setting'>
                  <FlagOwnerGroups projectId={projectId} id={projectFlag.id} />
                </FormGroup>
                <PlanBasedBanner
                  className='mb-3'
                  feature={'FLAG_OWNERS'}
                  theme={'description'}
                />
              </>
            )
          }
        </Permission>
      )}
      <FormGroup className='mb-3 setting'>
        <InputGroup
          value={projectFlag?.description || ''}
          data-test='featureDesc'
          inputProps={{
            className: 'full-width',
            name: 'featureDesc',
          }}
          onChange={(e: InputEvent) =>
            onChange({
              ...projectFlag,
              description: Utils.safeParseEventValue(e),
            })
          }
          ds
          type='text'
          title={identity ? 'Description' : 'Description (optional)'}
          placeholder="e.g. 'This determines what size the header is' "
        />
      </FormGroup>

      {!identity && (
        <FormGroup className='mb-3 mt-3 setting'>
          <Row>
            <Switch
              checked={projectFlag?.is_server_key_only || false}
              onChange={(is_server_key_only) =>
                onChange({ ...projectFlag, is_server_key_only })
              }
              className='ml-0'
            />
            <Tooltip
              title={
                <label className='cols-sm-2 control-label mb-0 ml-3'>
                  Server-side only <Icon name='info-outlined' />
                </label>
              }
            >
              Prevent this feature from being accessed with client-side SDKs.
            </Tooltip>
          </Row>
        </FormGroup>
      )}

      {!identity && isEdit && (
        <FormGroup className='mb-3 setting'>
          <Row>
            <Switch
              checked={projectFlag?.is_archived || false}
              onChange={(is_archived) =>
                onChange({ ...projectFlag, is_archived })
              }
              className='ml-0'
            />
            <Tooltip
              title={
                <label className='cols-sm-2 control-label mb-0 ml-3'>
                  Archived <Icon name='info-outlined' />
                </label>
              }
            >
              {`Archiving a flag allows you to filter out flags from the
                Flagsmith dashboard that are no longer relevant.
                <br />
                An archived flag will still return as normal in all SDK
                endpoints.`}
            </Tooltip>
          </Row>
        </FormGroup>
      )}
    </>
  )
}

export default FeatureSettings
