import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import React from 'react'

interface AddVariationButtonProps {
  disabled: boolean
  multivariateOptions: any[]
  onClick: () => void
}

export const AddVariationButton: React.FC<AddVariationButtonProps> = ({
  disabled,
  multivariateOptions,
  onClick,
}) => {
  return (
    <Button
      disabled={disabled}
      data-test='add-variation'
      type='button'
      size='xSmall'
      theme={multivariateOptions?.length ? 'primary' : 'outline'}
      onClick={onClick}
    >
      <Icon name='plus' width={16} />
      {multivariateOptions?.length ? 'Add variant' : 'Create A/B/n Test'}
    </Button>
  )
}
