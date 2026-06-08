import React, { FC, ReactNode } from 'react'

type StepShellProps = {
  body: ReactNode
  footer: ReactNode
  subtitle?: ReactNode
  title: string
}

const StepShell: FC<StepShellProps> = ({ body, footer, subtitle, title }) => (
  <section className='onboarding-quickstart__card rounded-lg border border-default bg-surface-default shadow-sm p-4 p-md-5'>
    <h2 className={subtitle ? 'mb-1' : 'mb-4'}>{title}</h2>
    {subtitle && <p className='text-muted mb-4'>{subtitle}</p>}

    <div className='onboarding-quickstart__step-body'>{body}</div>

    <div className='onboarding-quickstart__step-footer d-flex align-items-center justify-content-between mt-4 gap-2'>
      {footer}
    </div>
  </section>
)

export default StepShell
