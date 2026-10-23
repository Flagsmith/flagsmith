import React, { FC, ReactNode } from 'react'

type ConnectCohortProviderStepProps = {
  index: number
  title: string
  children: ReactNode
}

const ConnectCohortProviderStep: FC<ConnectCohortProviderStepProps> = ({
  children,
  index,
  title,
}) => (
  <div className='d-flex gap-3'>
    <span className='connect-cohort-provider__step-number bg-surface-action-subtle text-action rounded-full fs-captionSmall fw-bold d-flex align-items-center justify-content-center flex-shrink-0'>
      {index}
    </span>
    <div className='flex-fill'>
      <div className='fw-bold text-default mb-2'>{title}</div>
      {children}
    </div>
  </div>
)

export default ConnectCohortProviderStep
