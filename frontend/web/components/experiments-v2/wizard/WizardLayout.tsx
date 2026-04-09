import React, { FC, ReactNode } from 'react'
import './WizardLayout.scss'

type WizardLayoutProps = {
  sidebar: ReactNode
  children: ReactNode
}

const WizardLayout: FC<WizardLayoutProps> = ({ children, sidebar }) => {
  return (
    <div className='wizard-layout'>
      <aside className='wizard-layout__sidebar'>{sidebar}</aside>
      <div className='wizard-layout__content'>{children}</div>
    </div>
  )
}

WizardLayout.displayName = 'WizardLayout'
export default WizardLayout
