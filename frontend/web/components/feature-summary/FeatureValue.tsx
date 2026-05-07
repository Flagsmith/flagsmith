import { FC } from 'react'
import { FlagsmithValue } from 'common/types/responses'
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'
import { getViewMode } from 'common/useViewMode'
import classNames from 'classnames'

type FeatureValueType = {
  value: FlagsmithValue
  className?: string
  onClick?: () => void
  'data-test'?: string
}

const FeatureValue: FC<FeatureValueType> = (props) => {
  const isCompact = getViewMode() === 'compact'
  const chipClassName = classNames(
    `chip flex-row no-wrap ${props.className || ''}`,
    {
      'chip--sm justify-content-start': isCompact,
    },
  )

  if (props.value === null || props.value === undefined) {
    return (
      <div
        className={chipClassName}
        onClick={props.onClick}
        data-test={props['data-test']}
        style={{ maxWidth: 'fit-content' }}
      >
        <span className='feature-value text-muted'>[no value]</span>
      </div>
    )
  }

  const type = typeof props.value
  return (
    <div
      className={chipClassName}
      onClick={props.onClick}
      data-test={props['data-test']}
      style={{ maxWidth: 'fit-content' }}
    >
      {type == 'string' && <span className='quot'>"</span>}
      <span
        className='feature-value'
        style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}
      >
        {Format.truncateText(
          `${Utils.getTypedValue(props.value)}`,
          isCompact ? 24 : 20,
        )}
      </span>
      {type == 'string' && <span className='quot'>"</span>}
    </div>
  )
}

export default FeatureValue
