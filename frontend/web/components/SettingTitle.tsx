import React, { FC, PropsWithChildren } from 'react'
import classNames from 'classnames'
import { HeadingText } from './base/typography'

type SettingTitleType = PropsWithChildren<{
  danger?: boolean
}>

const SettingTitle: FC<SettingTitleType> = ({ children, danger }) => {
  return (
    <>
      <HeadingText
        level={2}
        className={classNames('mt-5 mb-0', { 'text-danger': danger })}
      >
        {children}
      </HeadingText>
      <hr className='py-0 my-3' />
    </>
  )
}

export default SettingTitle
