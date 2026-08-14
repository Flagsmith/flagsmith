import React, { FC, useEffect, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import ValueEditor from 'components/ValueEditor'
import Constants from 'common/constants'
import { VariationOptions } from 'components/mv/VariationOptions'
import { AddVariationButton } from 'components/mv/AddVariationButton'
import ErrorMessage from 'components/ErrorMessage'
import InfoMessage from 'components/InfoMessage'
import WarningMessage from 'components/WarningMessage'
import Tooltip from 'components/Tooltip'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'
import JSONReference from 'components/JSONReference'
import Button from 'components/base/forms/Button'
import CompareSegmentOverride from 'components/diff/CompareSegmentOverride'
import { FlagValueFooter } from 'components/modals/FlagValueFooter'
import Utils from 'common/utils/utils'
import {
  FeatureState,
  MultivariateOption,
  ProjectFlag,
} from 'common/types/responses'
import { FeatureExperimentFreeze } from 'common/hooks/useFeatureExperimentFreeze'
import ExperimentFreezeNotice from 'components/modals/create-feature/components/ExperimentFreezeNotice'
import { useHasPermission } from 'common/providers/Permission'
import { ProjectPermission } from 'common/types/permissions.types'

function isNegativeNumberString(str: any) {
  if (typeof Utils.getTypedValue(str) !== 'number') {
    return false
  }
  if (typeof str !== 'string') {
    return false
  }
  const num = parseFloat(str)
  return !isNaN(num) && num < 0
}

type FeatureValueTabProps = {
  error: any
  projectId: number | string
  identity?: string
  noPermissions: boolean
  freeze?: FeatureExperimentFreeze
  featureState: FeatureState
  projectFlag: ProjectFlag
  environmentFlag?: FeatureState
  environmentId?: string
  environmentName?: string
  is4Eyes?: boolean
  isVersioned?: boolean
  isSaving?: boolean
  existingChangeRequest?: boolean
  onSaveFeatureValue?: (schedule?: boolean) => void
  // The persisted variants, used to tag edited ones as not saved.
  originalMultivariateOptions?: MultivariateOption[]
  onEnvironmentFlagChange: (changes: Partial<FeatureState>) => void
  onProjectFlagChange: (changes: Partial<ProjectFlag>) => void
  onRemoveMultivariateOption?: (id: number) => void
}

// No tooltip when using variations (no single value to describe).
const getValueTooltip = (
  hasVariations: boolean,
  isEdit: boolean,
): string | undefined => {
  if (hasVariations) return undefined
  const seedsAllEnvironments = isEdit
    ? ''
    : '<br/>Setting this when creating a feature will set the value for all environments. You can edit this individually for each environment once the feature is created.'
  return `${Constants.strings.REMOTE_CONFIG_DESCRIPTION}${seedsAllEnvironments}`
}

const FeatureValueTab: FC<FeatureValueTabProps> = ({
  environmentFlag,
  environmentId,
  environmentName,
  error,
  existingChangeRequest,
  featureState,
  freeze,
  identity,
  is4Eyes,
  isSaving,
  isVersioned,
  noPermissions,
  onEnvironmentFlagChange,
  onProjectFlagChange,
  onRemoveMultivariateOption,
  onSaveFeatureValue,
  originalMultivariateOptions,
  projectFlag,
  projectId,
}) => {
  const isEdit = !!projectFlag?.id
  const isDisabled = !!noPermissions || !!freeze?.isFrozen

  const { permission: createFeature } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.CREATE_FEATURE,
  })

  const default_enabled = featureState.enabled ?? false
  const initial_value = featureState.feature_state_value
  const multivariate_options = projectFlag.multivariate_options || []
  const environmentVariations =
    featureState.multivariate_feature_state_values ?? []
  const identityVariations =
    featureState.multivariate_feature_state_values ?? []
  const controlPercentage = Utils.calculateControl(multivariate_options)
  const invalid =
    !!multivariate_options &&
    multivariate_options.length &&
    controlPercentage < 0

  const addVariation = () => {
    // Default the label to the first free Variant_n so new variants are
    // saved with a key even if the user never edits it. Variants with no
    // key display (and persist) their fallback, so avoid those names too.
    const existingNames = multivariate_options.map(
      (option, index) => option.key || Utils.getDefaultVariantKey(index),
    )
    let nextIndex = multivariate_options.length
    while (existingNames.includes(Utils.getDefaultVariantKey(nextIndex))) {
      nextIndex += 1
    }
    const newVariation = {
      ...Utils.valueToFeatureState(''),
      default_percentage_allocation: 0,
      key: Utils.getDefaultVariantKey(nextIndex),
    }
    onProjectFlagChange({
      multivariate_options: [...multivariate_options, newVariation],
    })
  }

  const [compareOpen, setCompareOpen] = useState(false)

  const [isNegativeNumber, setIsNegativeNumber] = useState(
    isNegativeNumberString(featureState?.feature_state_value),
  )

  useEffect(() => {
    setIsNegativeNumber(
      isNegativeNumberString(featureState?.feature_state_value),
    )
  }, [featureState?.feature_state_value])

  const handleRemoveVariation = (i: number) => {
    const idToRemove = multivariate_options[i].id

    const doRemove = () => {
      if (idToRemove && onRemoveMultivariateOption) {
        onRemoveMultivariateOption(idToRemove)
      }
      const newMultivariateOptions = multivariate_options.filter(
        (_, index) => index !== i,
      )
      onProjectFlagChange({
        multivariate_options: newMultivariateOptions,
      })
    }

    if (idToRemove) {
      openConfirm({
        body: 'This will remove the variation on your feature for all environments, if you wish to turn it off just for this environment you can set the % value to 0.',
        destructive: true,
        onYes: doRemove,
        title: 'Delete variation',
        yesText: 'Confirm',
      })
    } else {
      doRemove()
    }
  }

  const handleUpdateVariation = (
    i: number,
    updatedVariation: any,
    updatedEnvironmentVariations: any[],
  ) => {
    // Update the environment variations (weights)
    onEnvironmentFlagChange({
      multivariate_feature_state_values: updatedEnvironmentVariations,
    })

    // Update the multivariate option itself
    const newMultivariateOptions = [...multivariate_options]
    newMultivariateOptions[i] = updatedVariation
    onProjectFlagChange({
      multivariate_options: newMultivariateOptions,
    })
  }

  const enabledString = isEdit ? 'Enabled' : 'Enabled by default'

  const hasVariations = !!multivariate_options && !!multivariate_options.length

  // The Value tab compares the environment default against other environments
  // (and this environment's segment overrides). Multivariate features and
  // identity overrides are excluded.
  const canCompareValue =
    isEdit && !!environmentId && !identity && !hasVariations

  // Fields the user can change on a variant from this tab.
  const variantFields: (keyof MultivariateOption)[] = [
    'key',
    'type',
    'string_value',
    'integer_value',
    'boolean_value',
    'default_percentage_allocation',
  ]
  const unsavedVariations = multivariate_options.map((option) => {
    if (!originalMultivariateOptions) {
      return false
    }
    // A just-saved variant may not have its id reflected in local state
    // yet, so id-less options are matched against id-less baseline entries.
    const savedMvs = originalMultivariateOptions.filter((o) =>
      option.id ? o.id === option.id : !o.id,
    )
    return !savedMvs.some((savedMv) =>
      variantFields.every(
        (field) => (option[field] ?? null) === (savedMv[field] ?? null),
      ),
    )
  })

  const variationApiErrors = multivariate_options.map((_, i) => {
    const variationError = error?.multivariate_options?.[i]
    if (!variationError) {
      return null
    }
    if (typeof variationError === 'string') {
      return variationError
    }
    const firstField = Object.values(variationError)[0]
    return (
      (Array.isArray(firstField) ? firstField[0] : firstField) ||
      'Failed to save this variation.'
    )
  })
  const valueTitle = hasVariations ? (
    <span className='d-inline-flex align-items-center'>
      Control Value
      <span className='ml-1'>
        <Icon name='info-outlined' />
      </span>
      <span className='chip chip--xs ml-2'>
        {Math.max(0, controlPercentage)}%
      </span>
    </span>
  ) : (
    'Value'
  )

  const variationsInfo = hasVariations && (
    <p className='mb-4'>
      <InfoMessage collapseId={'variation-value'}>
        Changing a Variation Value will affect <strong>all environments</strong>
        , their weights are specific to this environment. Existing users will
        see the new variation value if it is changed. These values will only
        apply when you identify via the SDK.
        <a
          target='_blank'
          href='https://docs.flagsmith.com/basic-features/managing-features#multi-variate-flags'
          rel='noreferrer'
        >
          Check the Docs for more details
        </a>
        .
      </InfoMessage>
    </p>
  )

  const showValue = !(
    !!identity &&
    multivariate_options &&
    !!multivariate_options.length
  )

  if (compareOpen && canCompareValue && environmentId) {
    return (
      <div className={`${identity ? 'mx-3' : ''}`}>
        <div className='mb-3'>
          <Button
            theme='text'
            size='small'
            onClick={() => setCompareOpen(false)}
          >
            <Icon name='arrow-left' width={16} />
            Back to value
          </Button>
        </div>
        <CompareSegmentOverride
          projectId={projectId}
          environmentId={environmentId}
          featureId={projectFlag.id}
          source={{
            enabled: default_enabled,
            label: 'Environment Default',
            value: initial_value,
          }}
          sourceDescriptor={{ kind: 'environment' }}
        />
      </div>
    )
  }

  return (
    <div className={`${identity ? 'mx-3' : ''}`}>
      {freeze?.isFrozen && freeze.experiment && environmentId && (
        <ExperimentFreezeNotice
          experiment={freeze.experiment}
          projectId={projectId}
          environmentId={environmentId}
        />
      )}
      <FormGroup className='mb-4'>
        <Tooltip
          title={
            <div className='flex-row'>
              <Switch
                data-test='toggle-feature-button'
                defaultChecked={default_enabled}
                disabled={isDisabled}
                checked={default_enabled}
                onChange={(enabled) => onEnvironmentFlagChange({ enabled })}
                className='ml-0'
              />
              <div className='label-switch ml-3 mr-1'>
                {enabledString || 'Enabled'}
              </div>
              {!isEdit && <Icon name='info-outlined' />}
            </div>
          }
        >
          {!isEdit
            ? 'This will determine the initial enabled state for all environments. You can edit the this individually for each environment once the feature is created.'
            : ''}
        </Tooltip>
      </FormGroup>

      {showValue && (
        <FormGroup className='mb-4'>
          <InputGroup
            component={
              <ValueEditor
                data-test='featureValue'
                name='featureValue'
                className={`full-width${hasVariations ? ' code-medium' : ''}`}
                value={`${
                  typeof initial_value === 'undefined' || initial_value === null
                    ? ''
                    : initial_value
                }`}
                onChange={(e: any) => {
                  const feature_state_value = Utils.getTypedValue(
                    Utils.safeParseEventValue(e),
                  )
                  onEnvironmentFlagChange({ feature_state_value })
                }}
                disabled={isDisabled}
                placeholder="e.g. 'big' "
              />
            }
            tooltip={getValueTooltip(hasVariations, isEdit)}
            title={valueTitle}
          />
          {canCompareValue && (
            <div className='text-end mt-2'>
              <Button
                theme='text'
                size='small'
                data-test='compare-feature-value'
                onClick={() => setCompareOpen(true)}
              >
                <Icon name='difference' width={16} />
                Compare across environments
              </Button>
            </div>
          )}
        </FormGroup>
      )}

      {isNegativeNumber && (
        <WarningMessage
          warningMessage={
            <div>
              This feature currently has the value of{' '}
              <strong>"{featureState.feature_state_value}"</strong>. Saving this
              feature will convert its value from a string to a number. If you
              wish to preserve this value as a string, please save it using the{' '}
              <a href='https://api.flagsmith.com/api/v1/docs/#/api/api_v1_environments_featurestates_update'>
                API
              </a>
              .
            </div>
          }
        />
      )}

      {!!error?.initial_value?.[0] && (
        <div className='mx-2 mt-2'>
          <ErrorMessage error={error.initial_value[0]} />
        </div>
      )}

      {!!identity && (
        <div>
          <FormGroup className='mb-4'>
            {variationsInfo}
            <VariationOptions
              canCreateFeature={false}
              disabled
              select
              controlValue={
                projectFlag.environment_feature_state?.feature_state_value ??
                null
              }
              controlPercentage={controlPercentage}
              variationOverrides={identityVariations as any}
              setValue={(value) =>
                onEnvironmentFlagChange({ feature_state_value: value })
              }
              setVariations={(variations) =>
                onEnvironmentFlagChange({
                  multivariate_feature_state_values: variations as any,
                })
              }
              updateVariation={() => {}}
              weightTitle='Override Weight %'
              multivariateOptions={projectFlag.multivariate_options || []}
              removeVariation={() => {}}
            />
          </FormGroup>
        </div>
      )}

      {!identity && (
        <div>
          {variationsInfo}
          {hasVariations && (
            <Row className='justify-content-between align-items-center mb-2'>
              {Utils.getFlagsmithHasFeature('experimental_flags') ? (
                <Tooltip
                  title={
                    <label className='mb-0 cursor-pointer'>
                      Variants <Icon name='info-outlined' />
                    </label>
                  }
                >
                  To use this flag in an experiment, all the variants must have
                  a label.
                </Tooltip>
              ) : (
                <label className='mb-0'>Variants</label>
              )}
              {Utils.renderWithPermission(
                createFeature,
                Constants.projectPermissions(ProjectPermission.CREATE_FEATURE),
                <AddVariationButton
                  multivariateOptions={multivariate_options}
                  disabled={!createFeature || isDisabled}
                  onClick={addVariation}
                />,
              )}
            </Row>
          )}
          <FormGroup className='mb-0'>
            {(!!environmentVariations || !isEdit) && (
              <VariationOptions
                canCreateFeature={createFeature}
                disabled={!!identity || isDisabled}
                controlValue={featureState.feature_state_value}
                controlPercentage={controlPercentage}
                variationOverrides={environmentVariations as any}
                setValue={(value) =>
                  onEnvironmentFlagChange({ feature_state_value: value })
                }
                setVariations={(variations) =>
                  onEnvironmentFlagChange({
                    multivariate_feature_state_values: variations as any,
                  })
                }
                apiErrors={variationApiErrors}
                unsavedVariations={unsavedVariations}
                updateVariation={handleUpdateVariation}
                weightTitle={
                  isEdit ? 'Environment Weight %' : 'Default Weight %'
                }
                multivariateOptions={multivariate_options}
                removeVariation={handleRemoveVariation}
              />
            )}
          </FormGroup>
          {!hasVariations && (
            <div className='text-end'>
              {Utils.renderWithPermission(
                createFeature,
                Constants.projectPermissions(ProjectPermission.CREATE_FEATURE),
                <AddVariationButton
                  multivariateOptions={multivariate_options}
                  disabled={!createFeature || isDisabled}
                  onClick={addVariation}
                />,
              )}
            </div>
          )}
        </div>
      )}

      {environmentId &&
        onSaveFeatureValue &&
        !freeze?.isFrozen &&
        !freeze?.isLoading && (
          <>
            <JSONReference
              className='mb-3'
              showNamesButton
              title={'Feature'}
              json={projectFlag}
            />
            <JSONReference
              className='mb-3'
              title={'Feature state'}
              json={environmentFlag}
            />
            <FlagValueFooter
              is4Eyes={!!is4Eyes}
              isVersioned={!!isVersioned}
              projectId={
                typeof projectId === 'string'
                  ? parseInt(projectId, 10)
                  : projectId
              }
              projectFlag={projectFlag}
              environmentId={environmentId}
              environmentName={environmentName || ''}
              isSaving={!!isSaving}
              featureName={projectFlag.name}
              isInvalid={!!invalid}
              existingChangeRequest={!!existingChangeRequest}
              onSaveFeatureValue={onSaveFeatureValue}
            />
          </>
        )}
    </div>
  )
}

export default FeatureValueTab
