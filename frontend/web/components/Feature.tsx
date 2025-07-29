import React, { useCallback, useMemo } from 'react'
import ValueEditor from './ValueEditor'
import Constants from 'common/constants'
import VariationOptions from './mv/VariationOptions'
import AddVariationButton from './mv/AddVariationButton'
import ErrorMessage from './ErrorMessage'
import Tooltip from './Tooltip'
import Icon from './Icon'
import InputGroup from './base/forms/InputGroup'
import WarningMessage from './WarningMessage'
import Utils from 'common/utils/utils'
import Switch from './Switch'

import {
  FeatureState,
  ProjectFlag,
  FlagsmithValue,
} from 'common/types/responses'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import { useRouteContext } from './providers/RouteContext'

interface FeatureProps {
  checked?: boolean
  value?: any
  error?: any
  readOnly?: boolean
  isEdit?: boolean
  identity?: any
  projectId?: number
  projectFlag?: ProjectFlag
  environmentFlag?: FeatureState
  environmentVariations?: any[]
  multivariate_options?: any[]
  identityVariations?: any[]

  onCheckedChange?: (enabled: boolean) => void
  onValueChange?: (value: any) => void
  onChangeIdentityVariations?: (variations: any[]) => void
  removeVariation?: (index: number) => void
  updateVariation?: (index: number, variation: any) => void
  addVariation?: () => void

  hideAddVariation?: boolean
  canCreateFeature?: boolean
}

function isNegativeNumberString(value?: FlagsmithValue): boolean {
  if (!value) {
    return false
  }

  if (typeof Utils.getTypedValue(value) !== 'number') {
    return false
  }
  if (typeof value !== 'string') {
    return false
  }
  const num = parseFloat(value)
  return !isNaN(num) && num < 0
}

const Feature: React.FC<FeatureProps> = ({
  addVariation,
  canCreateFeature = true,
  checked = false,
  environmentFlag,
  environmentVariations = [],
  error,
  hideAddVariation = false,
  identity,
  identityVariations = [],
  isEdit = false,
  multivariate_options = [],
  onChangeIdentityVariations,
  onCheckedChange,
  onValueChange,
  projectFlag,
  projectId,
  readOnly = false,
  removeVariation,
  updateVariation,
  value,
}) => {
  const featureId = projectFlag?.id
  const { data: releasePipelines } = useGetReleasePipelinesQuery(
    {
      projectId: projectId ?? NaN,
    },
    {
      skip: !projectId,
    },
  )

  const isFeatureInReleasePipeline = useMemo(() => {
    if (!featureId) {
      return false
    }

    return releasePipelines?.results?.some((pipeline) =>
      pipeline.features?.includes(featureId),
    )
  }, [releasePipelines, featureId])

  const isNegativeNumberStr = isNegativeNumberString(
    environmentFlag?.feature_state_value,
  )

  const hasPermission =
    canCreateFeature && Utils.getPlansPermission('CREATE_FEATURE')
  const controlPercentage = Utils.calculateControl(multivariate_options)

  const enabledString = isEdit ? 'Enabled' : 'Enabled by default'

  const valueString = useMemo(() => {
    if (identity) {
      return 'User override'
    }
    if (multivariate_options && multivariate_options.length) {
      return `Control Value - ${controlPercentage}%`
    }
    return 'Value'
  }, [identity, multivariate_options, controlPercentage])

  const showValue = useMemo(() => {
    return !(
      !!identity &&
      multivariate_options &&
      !!multivariate_options.length
    )
  }, [identity, multivariate_options])

  const handleRemoveVariation = useCallback(
    (index: number) => {
      const idToRemove = multivariate_options[index]?.id

      if (idToRemove) {
        openConfirm({
          body: 'This will remove the variation on your feature for all environments, if you wish to turn it off just for this environment you can set the % value to 0.',
          destructive: true,
          onYes: () => {
            removeVariation?.(index)
          },
          title: 'Delete variation',
          yesText: 'Confirm',
        })

        return
      }

      removeVariation?.(index)
    },
    [multivariate_options, removeVariation],
  )

  return (
    <div>
      <div className='mb-4'>
        <Tooltip
          title={
            <div className='flex-row'>
              <Switch
                data-test='toggle-feature-button'
                defaultChecked={checked}
                disabled={readOnly || isFeatureInReleasePipeline}
                checked={checked}
                onChange={onCheckedChange}
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
            : isFeatureInReleasePipeline
            ? 'This feature is in a release pipeline and cannot be edited.'
            : ''}
        </Tooltip>
      </div>

      {showValue && (
        <div className='mb-4'>
          <InputGroup
            component={
              <ValueEditor
                data-test='featureValue'
                name='featureValue'
                className='full-width'
                value={`${
                  typeof value === 'undefined' || value === null ? '' : value
                }`}
                onChange={onValueChange}
                disabled={readOnly || isFeatureInReleasePipeline}
                placeholder="e.g. 'big' "
              />
            }
            tooltip={
              isFeatureInReleasePipeline
                ? 'This feature is in a release pipeline and cannot be edited.'
                : `${Constants.strings.REMOTE_CONFIG_DESCRIPTION}${
                    !isEdit
                      ? '<br/>Setting this when creating a feature will set the value for all environments. You can edit this individually for each environment once the feature is created.'
                      : ''
                  }`
            }
            title={`${valueString}`}
          />
        </div>
      )}

      {isNegativeNumberStr && (
        <WarningMessage
          warningMessage={
            <div>
              This feature currently has the value of{' '}
              <strong>"{environmentFlag?.feature_state_value}"</strong>. Saving
              this feature will convert its value from a string to a number. If
              you wish to preserve this value as a string, please save it using
              the{' '}
              <a href='https://api.flagsmith.com/api/v1/docs/#/api/api_v1_environments_featurestates_update'>
                API
              </a>
              .
            </div>
          }
        />
      )}

      {!!error && (
        <div className='mx-2 mt-2'>
          <ErrorMessage error={error} />
        </div>
      )}

      {!!identity && (
        <div>
          <div className='mb-4'>
            <VariationOptions
              disabled
              select
              controlValue={environmentFlag?.feature_state_value}
              controlPercentage={controlPercentage}
              variationOverrides={identityVariations}
              setVariations={onChangeIdentityVariations}
              updateVariation={() => {}}
              weightTitle='Override Weight %'
              multivariateOptions={projectFlag?.multivariate_options || []}
              removeVariation={() => {}}
              preventRemove={false}
              readOnlyValue={false}
              setValue={() => {}}
            />
          </div>
        </div>
      )}

      {!identity && (
        <div>
          <div className='mb-0'>
            {(!!environmentVariations || !isEdit) && (
              <VariationOptions
                disabled={!!identity || readOnly}
                controlValue={environmentFlag?.feature_state_value}
                controlPercentage={controlPercentage}
                variationOverrides={environmentVariations}
                updateVariation={updateVariation}
                weightTitle={
                  isEdit ? 'Environment Weight %' : 'Default Weight %'
                }
                multivariateOptions={multivariate_options}
                removeVariation={handleRemoveVariation}
                preventRemove={false}
                readOnlyValue={false}
                select={false}
                setValue={() => {}}
                setVariations={() => {}}
              />
            )}
          </div>
          {!hideAddVariation &&
            Utils.renderWithPermission(
              hasPermission,
              Constants.projectPermissions('Create Feature'),
              <AddVariationButton
                multivariateOptions={multivariate_options}
                disabled={!hasPermission || readOnly}
                onClick={addVariation}
              />,
            )}
        </div>
      )}
    </div>
  )
}

export default Feature
