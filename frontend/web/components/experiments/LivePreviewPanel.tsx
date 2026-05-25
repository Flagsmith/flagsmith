import { FC } from 'react'

const LivePreviewPanel: FC = () => {
  return (
    <div className='d-none d-xl-block' style={{ flexShrink: 0, width: 320 }}>
      <div className='card p-3'>
        <div
          className='text-muted fw-bold text-uppercase'
          style={{ fontSize: 11, letterSpacing: 1 }}
        >
          Live Preview
        </div>
      </div>
    </div>
  )
}

export default LivePreviewPanel
