import classNames from 'classnames'
import { FC, ReactNode } from 'react'
import {
  FeatureState,
  IdentityFeatureState,
  ProjectFlag,
} from 'common/types/responses'
import { getViewMode } from 'common/useViewMode'
import featureValuesEqual from 'common/featureValuesEqual'
import UsersIcon from './svg/UsersIcon'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'
import Icon from './Icon'
import TagValues from './tags/TagValues'
import SegmentsIcon from './svg/SegmentsIcon'
import FeatureValue from './FeatureValue'
import Switch from './Switch'
const width = [200, 48, 78]

type FeatureOverrideRowType = {
  dataTest: string
  onClick: () => void
  hasOverride?: boolean
  onToggle?: () => void
  hasUserOverride?: boolean
  hasSegmentOverride?: boolean
  cta?: ReactNode
  valueDataTest?: string
  toggleDataTest?: string
  projectFlag: ProjectFlag
  editPermission: boolean
  editPermissionDescription: string
  environmentFeatureState: FeatureState
  overrideFeatureState: FeatureState | IdentityFeatureState | null | undefined
}

const FeatureOverrideRow: FC<FeatureOverrideRowType> = ({
  cta,
  dataTest,
  editPermission,
  editPermissionDescription,
  environmentFeatureState,
  hasSegmentOverride,
  hasUserOverride,
  onClick,
  onToggle,
  overrideFeatureState,
  projectFlag,
  toggleDataTest,
  valueDataTest,
}) => {
  if (!environmentFeatureState || !projectFlag) {
    return null
  }
  const name = projectFlag.name
  const projectId = projectFlag.project
  const featureId = projectFlag.id
  const isCompact = getViewMode() === 'compact'
  const flagEnabled = environmentFeatureState.enabled
  const flagValue = environmentFeatureState.feature_state_value
  const actualEnabled = overrideFeatureState?.enabled
  const actualValue = overrideFeatureState?.feature_state_value
  const description = projectFlag.description
  const flagEnabledDifferent = actualEnabled !== flagEnabled
  const flagValueDifferent = !featureValuesEqual(actualValue, flagValue)
  const hasOverride =
    !overrideFeatureState || flagEnabledDifferent || flagValueDifferent

  const isMultiVariateOverride =
    !!flagValueDifferent &&
    !!projectFlag?.multivariate_options?.find(
      (v: any) => Utils.featureStateToValue(v) === actualValue,
    )

  return (
    <div
      className={classNames(
        `flex-row space list-item clickable py-2`,
        {
          'bg-primary-opacity-5': hasOverride || hasSegmentOverride,
        },
        {
          'list-item-xs':
            isCompact && !flagEnabledDifferent && !flagValueDifferent,
        },
      )}
      key={featureId}
      data-test={dataTest}
      onClick={onClick}
    >
      <Flex className='table-column pt-0'>
        <Row>
          <Flex>
            <Row
              className='font-weight-medium'
              style={{
                alignItems: 'start',
                lineHeight: 1,
                rowGap: 4,
                wordBreak: 'break-all',
              }}
            >
              {/*todo - reuse FeatureName when https://github.com/Flagsmith/flagsmith/pull/5809 is merged */}
              <Row>
                <span>
                  {description ? (
                    <Tooltip title={<span>{name}</span>}>{description}</Tooltip>
                  ) : (
                    name
                  )}
                </span>
                <Button
                  onClick={(e) => {
                    e?.stopPropagation()
                    e?.currentTarget?.blur()
                    Utils.copyToClipboard(name)
                  }}
                  theme='icon'
                  className='ms-2 me-2'
                >
                  <Icon name='copy' />
                </Button>
              </Row>
              <TagValues projectId={`${projectId}`} value={projectFlag!.tags} />
            </Row>
            {hasUserOverride ? (
              <div className='list-item-subtitle text-primary d-flex align-items-center'>
                <UsersIcon fill='#6837fc' width={16} className='me-1' />
                This feature is being overridden for this identity
              </div>
            ) : flagEnabledDifferent ? (
              <div data-test={dataTest} className='list-item-subtitle'>
                <Row>
                  <Flex>
                    {isMultiVariateOverride ? (
                      <span>
                        This flag is being overridden by a variation defined on
                        your feature, the control value is{' '}
                        <strong>{flagEnabled ? 'on' : 'off'}</strong> for this
                        user
                      </span>
                    ) : (
                      <span className='list-item-subtitle d-flex text-primary align-items-center'>
                        <SegmentsIcon
                          className='me-1'
                          width={16}
                          fill='#6837fc'
                        />
                        {`This flag is being overridden by a segment and would normally be`}
                        <div className='ph-1 ml-1 mr-1 fw-semibold'>
                          {flagEnabled ? 'on' : 'off'}
                        </div>{' '}
                        for this user
                      </span>
                    )}
                  </Flex>
                </Row>
              </div>
            ) : flagValueDifferent ? (
              isMultiVariateOverride ? (
                <div className='list-item-subtitle'>
                  <span className='flex-row'>
                    This feature is being overridden by a % variation in the
                    environment, the control value of this feature is{' '}
                    <FeatureValue
                      className='ml-1 chip--xs'
                      includeEmpty
                      value={`${flagValue}`}
                    />
                  </span>
                </div>
              ) : (
                <span className='d-flex list-item-subtitle text-primary align-items-center'>
                  <SegmentsIcon className='me-1' width={16} fill='#6837fc' />
                  {`This feature is being
                                                        overridden by a segment
                                                        and would normally be`}
                  <FeatureValue
                    className='ml-1 chip--xs'
                    includeEmpty
                    value={`${flagValue}`}
                  />{' '}
                  for this user
                </span>
              )
            ) : (
              getViewMode() === 'default' && (
                <div className='list-item-subtitle'>
                  Using environment defaults
                </div>
              )
            )}
          </Flex>
        </Row>
      </Flex>
      <div className='table-column' style={{ width: width[0] }}>
        <FeatureValue data-test={valueDataTest} value={actualValue!} />
      </div>
      <div
        className='table-column'
        style={{ width: width[1] }}
        onClick={(e) => e.stopPropagation()}
      >
        {Utils.renderWithPermission(
          editPermission,
          editPermissionDescription,
          <Switch
            disabled={!editPermission}
            data-test={toggleDataTest}
            checked={actualEnabled}
            onChange={onToggle}
          />,
        )}
      </div>
      <div
        className='table-column p-0'
        style={{ width: width[2] }}
        onClick={(e) => e.stopPropagation()}
      >
        {cta}
      </div>
    </div>
  )
}

export default FeatureOverrideRow
