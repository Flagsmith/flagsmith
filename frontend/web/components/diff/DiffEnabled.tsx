import React, { FC } from 'react'
import Switch from 'components/Switch'
import DiffRow from './DiffRow'

type DiffType = {
  oldValue: boolean
  newValue: boolean
}

const DiffEnabled: FC<DiffType> = ({ newValue, oldValue }) => {
  if (E2E) {
    return (
      <>
        <div data-test={'old-enabled'}>{`${oldValue}`}</div>
        <div data-test={'new-enabled'}>{`${newValue}`}</div>
      </>
    )
  }
  if (oldValue === newValue) {
    return <Switch checked={newValue} />
  }
  return (
    <>
      <DiffRow state='removed'>
        <Switch checked={oldValue} />
      </DiffRow>
      <DiffRow state='added'>
        <Switch checked={newValue} />
      </DiffRow>
    </>
  )
}

export default DiffEnabled
