import React, { FC } from 'react'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import InputGroup from 'components/base/forms/InputGroup'
import AddEditTags from 'components/tags/AddEditTags'
import { CreateProjectFlagType } from './CreateFlagValue'
import { Project } from 'common/types/responses'
import Utils from 'common/utils/utils'
import FlagOwners from 'components/FlagOwners'
import FlagOwnerGroups from 'components/FlagOwnerGroups'
import Switch from 'components/Switch'
import Icon from 'components/Icon'

type CreateFlagSettingsType = {
  identity?: string
  projectFlag: CreateProjectFlagType
  setProjectFlag: (projectFlag: CreateProjectFlagType) => void
  project: Project
}

const CreateFlagSettings: FC<CreateFlagSettingsType> = ({
  identity,
  project,
  projectFlag,
  setProjectFlag,
}) => {
  const { permission: isProjectAdmin } = useHasPermission({
    id: `${project.id}`,
    level: 'project',
    permission: 'ADMIN',
  })
  const { permission: canCreateFeature } = useHasPermission({
    id: `${project.id}`,
    level: 'project',
    permission: 'CREATE_FEATURE',
  })
  const isEdit = !!projectFlag.id
  return (
    <>
      {!identity && projectFlag.tags && (
        <FormGroup className='mb-5 setting'>
          <InputGroup
            title={identity ? 'Tags' : 'Tags (optional)'}
            tooltip={Constants.strings.TAGS_DESCRIPTION}
            component={
              <AddEditTags
                readOnly={!!identity || !canCreateFeature}
                projectId={`${project.id}`}
                value={projectFlag.tags}
                onChange={(tags) => setProjectFlag({ ...projectFlag, tags })}
              />
            }
          />
        </FormGroup>
      )}
      {!identity && isProjectAdmin && !!isEdit && (
        <>
          <FormGroup className='mb-5 setting'>
            <FlagOwners projectId={project.id} id={projectFlag.id} />
          </FormGroup>
          <FormGroup className='mb-5 setting'>
            <FlagOwnerGroups projectId={project.id} id={projectFlag.id} />
          </FormGroup>
        </>
      )}
      <FormGroup className='mb-5 setting'>
        <InputGroup
          value={projectFlag.description}
          data-test='featureDesc'
          inputProps={{
            className: 'full-width',
            name: 'featureDesc',
          }}
          onChange={(e: InputEvent) =>
            setProjectFlag({
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
        <FormGroup className='mb-5 setting'>
          <Row>
            <Switch
              checked={projectFlag.is_server_key_only}
              onChange={(is_server_key_only: boolean) =>
                setProjectFlag({ ...projectFlag, is_server_key_only })
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
        <FormGroup className='mb-5 setting'>
          <Row>
            <Switch
              checked={projectFlag.is_archived}
              onChange={(is_archived: boolean) => {
                setProjectFlag({ ...projectFlag, is_archived })
              }}
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

export default CreateFlagSettings
