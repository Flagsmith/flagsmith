import React, { FC } from 'react'
import Format from 'common/utils/format'
import Icon from './icons/Icon'

type IdentifierStringType = {
  value: string | undefined | null
}

const IdentifierString: FC<IdentifierStringType> = ({ value }) => {
  const display = Format.trimAndHighlightSpaces(value)
  if (
    display?.includes(Format.spaceDelimiter) ||
    display?.includes(Format.newLineDelimiter) ||
    display?.includes(Format.tabDelimiter)
  ) {
    return (
      <Tooltip
        title={
          <>
            {display}
            <Icon name='info' className='ms-1' />
          </>
        }
      >
        {`This identifier includes characters that could easily be missed.
          We have highlighted this with the following characters:
          
          Spaces: ${Format.spaceDelimiter}
          Tabs: ${Format.tabDelimiter}
          New lines: ${Format.newLineDelimiter}`}
      </Tooltip>
    )
  }
  return <>{display}</>
}

export default IdentifierString
