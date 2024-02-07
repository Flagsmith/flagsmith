import React, { FC } from 'react'
import Format from 'common/utils/format'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'
import { Form } from 'reactstrap'

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
            <IonIcon className='ms-1' icon={informationCircle} />
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
