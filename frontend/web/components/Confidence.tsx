import { FC } from 'react'
import cn from 'classnames'
import Utils from 'common/utils/utils'
import Format from 'common/utils/format'

type ConfidenceType = {
  pValue: number
}

const Confidence: FC<ConfidenceType> = ({ pValue }) => {
  const confidence = Utils.convertToPConfidence(pValue)
  const confidenceDisplay = Format.enumeration.get(confidence)

  const confidenceClass = cn({
    'text-danger': confidence === 'VERY_LOW' || confidence === 'LOW',
    'text-muted': !['VERY_LOW', 'LOW', 'HIGH', 'VERY_HIGH'].includes(
      confidence,
    ),
    'text-success': confidence === 'HIGH' || confidence === 'VERY_HIGH',
  })

  return <div className={confidenceClass}>{confidenceDisplay}</div>
}

export default Confidence
