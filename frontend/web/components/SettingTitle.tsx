import React, { FC, PropsWithChildren } from 'react'
import classNames from 'classnames'
import Text from './base/Text'

type SettingTitleType = PropsWithChildren<{
  danger?: boolean
}>

const SettingTitle: FC<SettingTitleType> = ({ children, danger }) => {
  return (
    <>
      <Text
        variant='h5'
        level={5}
        className={classNames('mt-5 mb-0', { 'text-danger': danger })}
      >
        {children}
      </Text>
      <hr className='py-0 my-3' />
    </>
  )
}

export default SettingTitle
