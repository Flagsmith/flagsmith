import React, { FC, PropsWithChildren } from 'react'
import classNames from 'classnames'

type SettingTitleType = PropsWithChildren<{
  danger?: boolean
}>

const SettingTitle: FC<SettingTitleType> = ({ children, danger }) => {
  return (
    <>
      <h5 className={classNames('mt-5 mb-0', { 'text-danger': danger })}>
        {children}
      </h5>
      <hr className='py-0 my-3' />
    </>
  )
}

export default SettingTitle
