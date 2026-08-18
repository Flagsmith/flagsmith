import { FC } from 'react'
import ContentCard from 'components/base/grid/ContentCard'

const LivePreviewPanel: FC = () => {
  return (
    <div className='d-none d-xl-block' style={{ flexShrink: 0, width: 320 }}>
      <ContentCard title='Live Preview'>
        <p className='text-muted fs-small mb-0'>Coming soon</p>
      </ContentCard>
    </div>
  )
}

export default LivePreviewPanel
