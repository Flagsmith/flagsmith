import React, { useEffect, useRef, useState } from 'react'
import { IonIcon } from '@ionic/react'
import { play } from 'ionicons/icons'

interface GifComponentProps {
  src: string
  className?: string
}

const GifComponent: React.FC<GifComponentProps> = ({ className, src }) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const imgRef = useRef<HTMLImageElement | null>(null)

  useEffect(() => {
    const img = imgRef.current
    const canvas = canvasRef.current
    if (img && canvas && !isPlaying) {
      const ctx = canvas.getContext('2d')
      img.onload = () => {
        if (ctx) {
          canvas.width = img.width
          canvas.height = img.height
          ctx.drawImage(img, 0, 0)
        }
      }
    }
  }, [isPlaying])

  const handlePlayClick = () => {
    setIsPlaying(!isPlaying)
  }

  return (
    <div style={styles.container}>
      {isPlaying ? (
        <img
          onClick={handlePlayClick}
          className={className}
          src={src}
          alt='Playing GIF'
          style={styles.gif}
        />
      ) : (
        <div
          onClick={handlePlayClick}
          className='rounded'
          style={styles.thumbnailContainer}
        >
          <canvas
            className={className}
            ref={canvasRef}
            style={styles.thumbnail}
          />
          <img
            className={className}
            ref={imgRef}
            src={src}
            alt='GIF'
            style={styles.hiddenImage}
          />
          <div
            className='bg-primary shadow text-white d-flex align-items-center justify-content-center'
            style={{
              borderRadius: 32,
              cursor: 'pointer',
              fontSize: 32,
              height: 64,
              left: '50%',
              position: 'absolute',
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: 64,
            }}
          >
            <IonIcon icon={play} style={{ marginLeft: 4 }} color='white' />
          </div>
        </div>
      )}
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: 'inline-block',
    position: 'relative',
  },
  gif: {
    display: 'block',
    width: '100%',
  },
  hiddenImage: {
    display: 'none',
  },
  thumbnail: {
    display: 'block',
    opacity: 0.8,
    width: '100%',
  },
  thumbnailContainer: {
    background: 'rgba(0, 0, 0, 0.2)',
    cursor: 'pointer',
    position: 'relative',
  },
}

export default GifComponent
