import React, { FC, useEffect, useState } from 'react'
import { ProjectFlag } from 'common/types/responses'
import Constants from 'common/constants'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import AddEditTags from 'components/tags/AddEditTags'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { useHasPermission } from 'common/providers/Permission'
import FlagOwners from 'components/FlagOwners'
import FlagOwnerGroups from 'components/FlagOwnerGroups'
import PlanBasedBanner from 'components/PlanBasedAccess'
import Switch from 'components/Switch'
import Tooltip from 'components/Tooltip'
import Icon from 'components/Icon'
import JSONReference from 'components/JSONReference'
import ModalHR from 'components/modals/ModalHR'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import FormGroup from 'components/base/grid/FormGroup'
import Row from 'components/base/grid/Row'
import AccountStore from 'common/stores/account-store'
import { ProjectPermission } from 'common/types/permissions.types'
import { getStore } from 'common/store'
import { getSupportedContentType } from 'common/services/useSupportedContentType'

type FeatureSettingsTabProps = {
  identity?: string
  projectId: number | string
  projectFlag: ProjectFlag | null
  isSaving?: boolean
  invalid?: boolean
  hasMetadataRequired?: boolean
  onChange: (projectFlag: ProjectFlag) => void
  onHasMetadataRequiredChange: (hasMetadataRequired: boolean) => void
  onSaveSettings?: () => void
}

const FeatureSettingsTab: FC<FeatureSettingsTabProps> = ({
  hasMetadataRequired,
  identity,
  invalid,
  isSaving,
  onChange,
  onHasMetadataRequiredChange,
  onSaveSettings,
  projectFlag,
  projectId,
}) => {
  const [featureContentType, setFeatureContentType] = useState<any>({})

  const metadataEnable = Utils.getPlansPermission('METADATA')
  const isEdit = !!projectFlag?.id

  useEffect(() => {
    if (metadataEnable) {
      getSupportedContentType(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        const contentType = Utils.getContentType(res.data, 'model', 'feature')
        setFeatureContentType(contentType)
      })
    }
  }, [metadataEnable])

  const { permission: createFeature } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.CREATE_FEATURE,
  })

  if (!createFeature) {
    return (
      <InfoMessage>
        <div
          dangerouslySetInnerHTML={{
            __html: Constants.projectPermissions(
              ProjectPermission.CREATE_FEATURE,
            ),
          }}
        />
      </InfoMessage>
    )
  }

  if (!projectFlag) {
    return null
  }

  return (
    <div className={`${identity ? 'mx-3' : ''}`}>
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
      {metadataEnable && featureContentType?.id && !identity && (
        <>
          <label className='mt-1'>Custom Fields</label>
          <AddMetadataToEntity
            organisationId={AccountStore.getOrganisation().id}
            projectId={
              typeof projectId === 'string'
                ? parseInt(projectId, 10)
                : projectId
            }
            entityId={projectFlag?.id}
            entityContentType={featureContentType?.id}
            entity={featureContentType?.model}
            setHasMetadataRequired={onHasMetadataRequiredChange}
            onChange={(metadata) => onChange({ ...projectFlag, metadata })}
          />
        </>
      )}
      {!identity && projectFlag?.id && createFeature && (
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
      )}
      <FormGroup className='mb-3 setting'>
        <InputGroup
          value={projectFlag?.description || ''}
          data-test='featureDesc'
          inputProps={{
            className: 'full-width',
            name: 'featureDesc',
            readOnly: !!identity,
          }}
          onChange={(e: InputEvent) =>
            onChange({
              ...projectFlag,
              description: Utils.safeParseEventValue(e),
            })
          }
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

      {onSaveSettings && (
        <>
          <JSONReference
            className='mb-3'
            showNamesButton
            title={'Feature'}
            json={projectFlag}
          />
          <ModalHR className='mt-4' />
          {isEdit && (
            <div className='text-right mt-3'>
              {createFeature && (
                <>
                  <p className='text-right modal-caption fs-small lh-sm'>
                    This will save the above settings{' '}
                    <strong>all environments</strong>.
                  </p>
                  <Button
                    onClick={onSaveSettings}
                    data-test='update-feature-btn'
                    id='update-feature-btn'
                    disabled={
                      isSaving ||
                      !projectFlag.name ||
                      invalid ||
                      hasMetadataRequired
                    }
                  >
                    {isSaving ? 'Updating' : 'Update Settings'}
                  </Button>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default FeatureSettingsTab
