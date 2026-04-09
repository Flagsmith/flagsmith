import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import './WizardHeader.scss'

type BreadcrumbItem = {
  label: string
  href?: string
}

type WizardHeaderProps = {
  breadcrumbs: BreadcrumbItem[]
  title: string
  onCancel: () => void
}

const WizardHeader: FC<WizardHeaderProps> = ({
  breadcrumbs,
  onCancel,
  title,
}) => {
  return (
    <div className='wizard-header'>
      <div className='wizard-header__breadcrumb'>
        {breadcrumbs.map((item, index) => (
          <React.Fragment key={index}>
            <span className='wizard-header__breadcrumb-item'>{item.label}</span>
            {index < breadcrumbs.length - 1 && (
              <span className='wizard-header__breadcrumb-separator'>/</span>
            )}
          </React.Fragment>
        ))}
      </div>
      <div className='wizard-header__title-row'>
        <h1 className='wizard-header__title'>{title}</h1>
        <Button theme='outline' size='small' onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  )
}

WizardHeader.displayName = 'WizardHeader'
export default WizardHeader
