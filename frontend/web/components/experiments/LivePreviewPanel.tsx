import { FC } from 'react'
import ContentCard from 'components/base/grid/ContentCard'
import './wizard.scss'

const LivePreviewPanel: FC = () => {
  return (
    <div className='d-none d-xl-block wizard-preview-panel'>
      <ContentCard title='Live Preview'>
        <p className='text-muted fs-small mb-0'>Coming soon</p>
      </ContentCard>
    </div>
  )
}

export default LivePreviewPanel
