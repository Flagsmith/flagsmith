import { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'

type FeatureNameType = {
  name: string
}

const FeatureName: FC<FeatureNameType> = ({ name }) => {
  const copyFeature = () => {
    Utils.copyToClipboard(name)
  }
  return (
    <Row
      className='font-weight-medium'
      style={{
        lineHeight: 1,
        wordBreak: 'break-all',
      }}
    >
      <span>{name}</span>
      <Button onClick={copyFeature} theme='icon' className='ms-2 me-2'>
        <Icon name='copy' />
      </Button>
    </Row>
  )
}

export default FeatureName
