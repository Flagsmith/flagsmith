import React from 'react'

export default function AddVariationButton({ disabled, onClick }) {
  return (
    <div className='text-center'>
      <button
        disabled={disabled}
        data-test='add-variation'
        type='button'
        onClick={onClick}
        className='btn btn--outline'
      >
        Add Variation
      </button>
    </div>
  )
}
