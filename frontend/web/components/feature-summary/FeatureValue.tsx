import { FC } from 'react'
import { useFlags } from '@flagsmith/flagsmith/react'
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

const FeatureValue: FC<FeatureValueType> = ({
  className,
  'data-test': dataTest,
  onClick,
  value,
}) => {
  const isCompact = getViewMode() === 'compact'
  const flags = useFlags(['display_feature_null_values'])
  const showNullIndication = !!flags.display_feature_null_values?.enabled
  const isNull = value === null || value === undefined
  const isEmptyString = value === ''

  if ((isNull || isEmptyString) && !showNullIndication) {
    return null
  }

  const chipClassName = classNames(`chip flex-row no-wrap ${className || ''}`, {
    'chip--sm justify-content-start': isCompact,
  })
  const chipProps = {
    className: chipClassName,
    'data-test': dataTest,
    onClick,
    style: { maxWidth: 'fit-content' },
  }

  if (isNull) {
    return (
      <div {...chipProps}>
        <span className='feature-value text-muted'>[no value]</span>
      </div>
    )
  }

  if (isEmptyString) {
    return (
      <div {...chipProps}>
        <code className='feature-value text-info'>""</code>
      </div>
    )
  }

  const type = typeof value
  return (
    <div {...chipProps}>
      {type === 'string' && <span className='quot'>"</span>}
      <span
        className='feature-value'
        style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}
      >
        {Format.truncateText(
          `${Utils.getTypedValue(value)}`,
          isCompact ? 24 : 20,
        )}
      </span>
      {type === 'string' && <span className='quot'>"</span>}
    </div>
  )
}

export default FeatureValue
