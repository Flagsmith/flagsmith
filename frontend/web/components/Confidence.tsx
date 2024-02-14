import { FC } from 'react'
import Utils from 'common/utils/utils'
import Format from 'common/utils/format'

type ConfidenceType = {
  pValue: number
}

const Confidence: FC<ConfidenceType> = ({ pValue }) => {
  const confidence = Utils.convertToPConfidence(pValue)
  const confidenceDisplay = Format.enumeration.get(confidence)
  switch (confidence) {
    case 'VERY_LOW':
    case 'LOW':
      return <div className='text-danger'>{confidenceDisplay}</div>
    case 'HIGH':
    case 'VERY_HIGH':
      return <div className='text-success'>{confidenceDisplay}</div>
    default:
      return <div className='text-muted'>{confidenceDisplay}</div>
  }
}

export default Confidence
