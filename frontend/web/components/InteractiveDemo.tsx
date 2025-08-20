import React, { FC, useEffect } from 'react'
import { AppFeature } from 'common/utils/utils'
import { IonIcon } from '@ionic/react'
import { playCircle } from 'ionicons/icons'
import Button from './base/forms/Button'
const DEMO_URLS: Partial<Record<AppFeature, string>> = {
  FEATURE_HEALTH:
    'https://app.howdygo.com/embed/2bf57f95-2594-4aa9-82d4-0c8f299af148',
}

type InteractiveDemoProps = {
  feature: AppFeature
}

const InteractiveDemo: FC<InteractiveDemoProps> = ({ feature }) => {
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://js.howdygo.com/v1.2.1/index.js'
    script.async = true
    document.body.appendChild(script)
    return () => {
      document.body.removeChild(script)
    }
  }, [])
  const url = DEMO_URLS[feature]
  if (!url) return null

  const handleViewDemo = () => {
    openModal(
      '',
      <div
        id='howdygo-wrapper'
        className='bg-body'
        style={{
          aspectRatio: '2560 / 1308',
          borderRadius: '12px',
          boxSizing: 'content-box',
          maxWidth: '80vw',
          overflow: 'hidden',
          paddingBottom: '10px',
          position: 'relative',
        }}
      >
        <iframe
          id='howdygo-frame'
          src={url}
          allowFullScreen
          className='rounded'
          allow='clipboard-write'
          style={{
            height: '100%',
            left: 0,
            position: 'absolute',
            top: 0,
            width: '100%',
          }}
        ></iframe>
      </div>,
      'modal-full-screen',
    )
  }

  return (
    <Button theme='text' onClick={handleViewDemo}>
      <div className='d-flex align-items-center'>
        <IonIcon icon={playCircle} />
        View Demo
      </div>
    </Button>
  )
}

export default InteractiveDemo
