import React, { FC } from 'react'
import classNames from 'classnames'
import Switch from 'components/Switch'

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
      <div className={'flex-row'}>
        <div className='react-diff-marker react-diff-marker--removed'>
          <pre>-</pre>
        </div>
        <div className='react-diff-line react-diff-line--removed pe-2 flex-fill'>
          <Switch checked={oldValue} />
        </div>
      </div>
      <div className={'flex-row'}>
        <div className='react-diff-marker react-diff-marker--added'>
          <pre>+</pre>
        </div>
        <div className='react-diff-line react-diff-line--added pe-2 flex-fill'>
          <Switch checked={newValue} />
        </div>
      </div>
    </>
  )
}

export default DiffEnabled
