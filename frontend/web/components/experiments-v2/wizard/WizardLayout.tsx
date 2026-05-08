import React, { FC, ReactNode } from 'react'
import './WizardLayout.scss'

type WizardLayoutProps = {
  sidebar: ReactNode
  children: ReactNode
  preview?: ReactNode
}

const WizardLayout: FC<WizardLayoutProps> = ({
  children,
  preview,
  sidebar,
}) => {
  return (
    <div
      className={`wizard-layout${
        preview ? ' wizard-layout--with-preview' : ''
      }`}
    >
      <aside className='wizard-layout__sidebar'>{sidebar}</aside>
      <div className='wizard-layout__content'>{children}</div>
      {preview && <aside className='wizard-layout__preview'>{preview}</aside>}
    </div>
  )
}

WizardLayout.displayName = 'WizardLayout'
export default WizardLayout
