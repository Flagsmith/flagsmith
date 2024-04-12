import React, { FC } from 'react'
import { FeatureState, Project, ProjectFlag } from 'common/types/responses'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import ExistingChangeRequestAlert from 'components/ExistingChangeRequestAlert'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import useRegexValid from 'common/useRegexValid'
import InfoMessage from 'components/InfoMessage'
import ErrorMessage from 'components/ErrorMessage'

export type CreateProjectFlagType = Omit<
  ProjectFlag,
  'created_date' | 'id' | 'uuid' | 'project'
> & {
  id?: number
  uuid?: string
  project?: number
}

export type CreateFeatureStateType = Pick<
  FeatureState,
  'enabled' | 'multivariate_feature_state_values' | 'feature_state_value'
> &
  Partial<FeatureState>

type CreateFlagValueType = {
  error?: any
  project: Project
  environmentApiKey: string
  projectFlag: CreateProjectFlagType
  setProjectFlag: (projectFlag: CreateProjectFlagType) => void
}

const CreateFlagValue: FC<CreateFlagValueType> = ({
  environmentApiKey,
  error,
  project,
  projectFlag,
  setProjectFlag,
}) => {
  const caseSensitive = project?.only_allow_lower_case_feature_names
  const regexValid = useRegexValid(projectFlag.name, project.feature_name_regex)
  const environment = project?.environments?.find(
    (environment) => environment.api_key === environmentApiKey,
  )

  if (!environment) return null

  const isEdit = !!projectFlag?.id
  const onRef = (e: InstanceType<typeof InputGroup>) => {
    if (!isEdit) {
      setTimeout(() => {
        e?.focus()
      }, 500)
    }
  }
  const onNameChange = (e: InputEvent) => {
    const newName = Utils.safeParseEventValue(e).replace(/ /g, '_')
    setProjectFlag({
      ...projectFlag,
      name: caseSensitive ? newName.toLowerCase() : newName,
    })
  }
  return (
    <>
      {isEdit && (
        <Tooltip
          title={
            <h5 className='mb-4'>
              Environment Value <Icon name='info-outlined' />
            </h5>
          }
          place='top'
        >
          {Constants.strings.ENVIRONMENT_OVERRIDE_DESCRIPTION(environment.name)}
        </Tooltip>
      )}
      {projectFlag.id && (
        <ExistingChangeRequestAlert
          className='mb-4'
          featureId={projectFlag.id}
          environmentId={environmentApiKey}
        />
      )}
      {!isEdit && (
        <FormGroup className='mb-4 mt-2'>
          <InputGroup
            ref={onRef}
            data-test='featureID'
            inputProps={{
              className: 'full-width',
              maxLength: Constants.forms.maxLength.FEATURE_ID,
              name: 'featureID',
              readOnly: isEdit,
            }}
            value={projectFlag?.name}
            onChange={onNameChange}
            isValid={!!projectFlag.name && regexValid}
            type='text'
            title={
              <>
                <Tooltip
                  title={
                    <Row>
                      <span className={'mr-1'}>{isEdit ? 'ID' : 'ID*'}</span>
                      <Icon name='info-outlined' />
                    </Row>
                  }
                >
                  The ID that will be used by SDKs to retrieve the feature value
                  and enabled state. This cannot be edited once the feature has
                  been created.
                </Tooltip>
                {!!project.feature_name_regex && !isEdit && (
                  <div className='mt-2'>
                    <InfoMessage>
                      This must conform to the regular expression{' '}
                      <pre>{project.feature_name_regex}</pre>
                    </InfoMessage>
                  </div>
                )}
              </>
            }
            placeholder='E.g. header_size'
          />
          <ErrorMessage error={error?.name?.[0]} />
        </FormGroup>
      )}
    </>
  )
}

export default CreateFlagValue
