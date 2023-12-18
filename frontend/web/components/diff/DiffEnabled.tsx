import React, { FC } from 'react'
import classNames from 'classnames'
import Switch from 'components/Switch'

type DiffType = {
  oldValue: boolean
  newValue: boolean
}

const DiffEnabled: FC<DiffType> = ({ newValue, oldValue }) => {
  if (oldValue === newValue) {
    return <Switch checked={newValue} />
  }
  return (
    <>
      <div className={'git-diff git-diff--removed'}>
        - <Switch checked={oldValue} />
      </div>
      <div className={'git-diff git-diff--added'}>
        + <Switch checked={newValue} />
      </div>
    </>
  )
}

export default DiffEnabled
