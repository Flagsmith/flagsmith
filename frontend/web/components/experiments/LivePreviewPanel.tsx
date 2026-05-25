import { FC } from 'react'
import ContentCard from 'components/base/grid/ContentCard'

const LivePreviewPanel: FC = () => {
  return (
    <div className='d-none d-xl-block' style={{ flexShrink: 0, width: 320 }}>
      <ContentCard title='Live Preview'>
        <p className='text-muted mb-0' style={{ fontSize: 13 }}>
          Coming soon
        </p>
      </ContentCard>
    </div>
  )
}

export default LivePreviewPanel
