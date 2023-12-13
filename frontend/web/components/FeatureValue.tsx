import { FC } from 'react'
import { FlagsmithValue } from 'common/types/responses'
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'
import { getViewMode } from 'common/useViewMode'
import classNames from 'classnames' // we need this to make JSX compile

type FeatureValueType = {
  value: FlagsmithValue
  includeEmpty?: boolean // whether to show empty values
  className?: string
  onClick?: () => void
  'data-test'?: string
}

const FeatureValue: FC<FeatureValueType> = (props) => {
  if (props.value === null || props.value === undefined) {
    return null
  }
  const type = typeof props.value
  if (type === 'string' && props.value === '' && !props.includeEmpty) {
    return null
  }
  const isCompact = getViewMode() === 'compact'
  return (
    <span
      className={classNames(`chip ${props.className || ''}`, {
        'chip--sm justify-content-start d-inline': isCompact,
      })}
      onClick={props.onClick}
      data-test={props['data-test']}
    >
      {type == 'string' && <span className='quot'>"</span>}
      <span className='feature-value'>
        {Format.truncateText(
          `${Utils.getTypedValue(props.value)}`,
          isCompact ? 24 : 20,
        )}
      </span>
      {type == 'string' && <span className='quot'>"</span>}
    </span>
  )
}

export default FeatureValue
