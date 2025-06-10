import React, { FC } from 'react'
import { Resource } from './data/onboarding.data'

const GettingStartedResource: FC<Resource> = ({
  description,
  image,
  title,
  url,
}) => {
  return (
    <a href={url} target='_blank' className='' rel='noreferrer'>
      <div className='card bg-card p-0 h-100 border-1 rounded'>
        <div className='d-flex align-items-center'>
          <div>
            <img
              style={{
                aspectRatio: '155 / 200',
                height: 150,
                objectFit: 'cover',
                objectPosition: 'top',
              }}
              className=' rounded'
              {...image}
            />
          </div>
          <div className='h-100 d-flex flex-column justify-content-center p-3'>
            <h6 className={`d-flex align-items-center gap-1`}>{title}</h6>

            <span className='fw-normal fs-small  text-muted '>
              {description}
            </span>
          </div>
        </div>
      </div>
    </a>
  )
}

export default GettingStartedResource
