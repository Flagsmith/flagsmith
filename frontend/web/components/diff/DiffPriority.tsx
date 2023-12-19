import React, { FC } from 'react'
import classNames from 'classnames'
import Switch from 'components/Switch'

type DiffType = {
  oldValue: number
  newValue: number
}

const DiffPriority: FC<DiffType> = ({ newValue, oldValue }) => {
  let inner = null

  if (oldValue > newValue) {
    inner = (
      <div className={'position-change position-change--down'}>-{newValue}</div>
    )
  } else if (oldValue < newValue) {
    inner = (
      <div className={'position-change position-change--down'}>-{newValue}</div>
    )
  }
  return (
    <>
      {newValue}
      {inner}
    </>
  )
}

export default DiffPriority
