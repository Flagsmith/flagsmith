import classNames from 'classnames'
import Switch from './Switch'
import {
  FeatureListProviderData,
  FeatureState,
  ProjectFlag,
} from 'common/types/responses'
import FeatureValue from './FeatureValue'
import SegmentOverridesIcon from './SegmentOverridesIcon'
import IdentityOverridesIcon from './IdentityOverridesIcon'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'

export interface CondensedFeatureRowProps {
  disableControls?: boolean
  readOnly: boolean
  projectFlag: ProjectFlag
  environmentFlags: FeatureListProviderData['environmentFlags']
  permission?: boolean
  editFeature: (
    projectFlag: ProjectFlag,
    environmentFlag?: FeatureState,
    tab?: string,
  ) => void
  onChange: () => void
  style?: React.CSSProperties
  className?: string
  isCompact?: boolean
  fadeEnabled?: boolean
  fadeValue?: boolean
  hasUnhealthyEvents?: boolean
  index: number
}

const CondensedFeatureRow: React.FC<CondensedFeatureRowProps> = ({
  className,
  disableControls,
  editFeature,
  environmentFlags,
  fadeEnabled,
  fadeValue,
  hasUnhealthyEvents,
  index,
  isCompact,
  onChange,
  permission,
  projectFlag,
  readOnly,
  style,
}) => {
  const { id } = projectFlag
  const showPlusIndicator =
    projectFlag?.is_num_identity_overrides_complete === false

  return (
    <Flex
      onClick={() => {
        if (disableControls) return
        !readOnly &&
          editFeature(
            projectFlag,
            environmentFlags?.[id],
            hasUnhealthyEvents
              ? Constants.featurePanelTabs.FEATURE_HEALTH
              : undefined,
          )
      }}
      style={{ ...style }}
      className={classNames('flex-row', { 'fs-small': isCompact }, className)}
    >
      <div
        className={`table-column ${fadeEnabled && 'faded'}`}
        style={{ width: '80px' }}
      >
        <Row>
          <Switch
            disabled={!permission || readOnly}
            data-test={`feature-switch-${index}${
              environmentFlags?.[id].enabled ? '-on' : '-off'
            }`}
            checked={environmentFlags?.[id]?.enabled}
            onChange={onChange}
          />
        </Row>
      </div>
      <Flex className='table-column clickable'>
        <Row>
          <div
            onClick={() =>
              permission &&
              !readOnly &&
              editFeature(projectFlag, environmentFlags?.[id])
            }
            className={`flex-fill ${fadeValue ? 'faded' : ''}`}
          >
            <FeatureValue
              value={environmentFlags?.[id]?.feature_state_value ?? null}
              data-test={`feature-value-${index}`}
            />
          </div>

          <SegmentOverridesIcon
            onClick={(e) => {
              e.stopPropagation()
              editFeature(
                projectFlag,
                environmentFlags?.[id],
                Constants.featurePanelTabs.SEGMENT_OVERRIDES,
              )
            }}
            count={projectFlag.num_segment_overrides}
          />
          <IdentityOverridesIcon
            onClick={(e) => {
              e.stopPropagation()
              editFeature(
                projectFlag,
                environmentFlags?.[id],
                Constants.featurePanelTabs.IDENTITY_OVERRIDES,
              )
            }}
            count={projectFlag.num_identity_overrides}
            showPlusIndicator={showPlusIndicator}
          />
        </Row>
      </Flex>
    </Flex>
  )
}

export default CondensedFeatureRow
