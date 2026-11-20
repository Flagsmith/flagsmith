import { FC, ReactNode } from 'react'
import Banner from 'components/base/Banner'
import {
  PrerequisiteRow,
  describeOffCount,
  isBlocked,
} from './prerequisiteState'

type BlockedBannerProps = {
  environmentName: string
  rows: PrerequisiteRow[]
  action?: ReactNode
}

// Only rendered when the flag is held off. A flag serving its own value needs
// no announcement.
const BlockedBanner: FC<BlockedBannerProps> = ({
  action,
  environmentName,
  rows,
}) =>
  isBlocked(rows) ? (
    <Banner
      type='warning'
      className='mb-3'
      title={`Serving off in ${environmentName}`}
      action={action}
    >
      {describeOffCount(rows)}
    </Banner>
  ) : null

export default BlockedBanner
