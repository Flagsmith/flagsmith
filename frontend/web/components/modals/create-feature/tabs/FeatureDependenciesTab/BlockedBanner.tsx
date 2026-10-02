import { FC } from 'react'
import Banner from 'components/base/Banner'
import {
  PrerequisiteRow,
  describeOffCount,
  isBlocked,
} from './prerequisiteState'

type BlockedBannerProps = {
  environmentName: string
  rows: PrerequisiteRow[]
}

// Only rendered when the flag is held off. A flag serving its own value needs
// no announcement.
const BlockedBanner: FC<BlockedBannerProps> = ({ environmentName, rows }) =>
  isBlocked(rows) ? (
    <Banner
      type='warning'
      className='mb-3'
      title={`Serving off in ${environmentName}`}
    >
      {describeOffCount(rows)}
    </Banner>
  ) : null

export default BlockedBanner
