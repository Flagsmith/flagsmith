import { FC } from 'react'
import { FlagsmithValue } from 'common/types/responses'
import Format from 'common/utils/format' // we need this to make JSX compile

type FeatureValueType = {
  value: FlagsmithValue
  includeEmpty?: boolean // whether to show empty values
  className?: string
  onClick?: () => void
  'data-test'?: string
}

const FeatureValue: FC<FeatureValueType> = (props) => {
  const type = typeof props.value

  return (
    <span
      className={`chip ${props.className || ''}`}
      onClick={props.onClick}
      data-test={props['data-test']}
    >
      {type == 'string' && <span className='quot'>"</span>}
      <span className='feature-value'>
        {Format.truncateText(`${props.value}`, 20)}
      </span>
      {type == 'string' && <span className='quot'>"</span>}
    </span>
  )
}

export default FeatureValue
