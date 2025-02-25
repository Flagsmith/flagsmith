import React, { FC } from 'react'
import { IonIcon } from '@ionic/react'
import {
  book,
  checkmarkCircle,
  document,
  chatbox,
  bookSharp,
} from 'ionicons/icons'

type ResourcesType = {}

const Resources: FC<ResourcesType> = ({}) => {
  return (
    <div>
      <div className='rounded border-1 p-2 text-primary'>
        <h6 className='d-flex mb-0 fs-captionXSmall letter-spacing text-muted  align-items-center gap-2'>
          <IonIcon className='' icon={bookSharp} />
          <span className='fw-semibold'>RESOURCES</span>
        </h6>
        <hr className='mt-1' />
        <div className='mt-1'>
          <div className='d-flex flex-column gap-2 my-2'>
            <a className='text-primary d-flex align-items-center gap-1' href=''>
              <IonIcon className='' icon={chatbox} />
              Ask a question
            </a>
            <a className='text-primary d-flex align-items-center gap-1' href=''>
              <IonIcon className='' icon={document} />
              Docs
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Resources
