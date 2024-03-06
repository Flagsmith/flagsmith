import Button from 'components/base/forms/Button'
import React from 'react'

export default function AddVariationButton({
  disabled,
  multivariateOptions,
  onClick,
}) {
  return (
    <div className='text-end'>
      <Button
        disabled={disabled}
        data-test='add-variation'
        type='button'
        onClick={onClick}
        theme='outline'
      >
        {multivariateOptions?.length ? 'Add Variation' : 'Create A/B/n Test'}
      </Button>
    </div>
  )
}
