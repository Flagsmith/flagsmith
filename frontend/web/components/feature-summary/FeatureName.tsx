import { FC } from 'react'
import IconButton from 'components/base/IconButton'
import Utils from 'common/utils/utils'
import { CopyIcon } from 'components/icons'

type FeatureNameType = {
  name: string
}

const FeatureName: FC<FeatureNameType> = ({ name }) => {
  const copyFeature = (e: React.MouseEvent) => {
    e.stopPropagation()
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
      <IconButton
        variant='ghost'
        size='small'
        aria-label='Copy feature name'
        onClick={copyFeature}
        className='ms-2 me-2'
      >
        <CopyIcon width={16} />
      </IconButton>
    </Row>
  )
}

export default FeatureName
