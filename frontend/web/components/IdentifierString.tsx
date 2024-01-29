import React, { FC } from 'react'
import Format from 'common/utils/format'
import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'

type IdentifierStringType = {
  value: string | undefined | null
}

const IdentifierString: FC<IdentifierStringType> = ({ value }) => {
  const display = Format.trimAndHighlightSpaces(value)
  if (display?.includes(Format.spaceDelimiter)) {
    return (
      <Tooltip
        title={
          <>
            {display}
            <IonIcon className='ms-1' icon={informationCircle} />
          </>
        }
      >
        {`This identifier includes whitespace that could easily be missed.
          We have highlighted this with the character${' '}
          <strong>${Format.spaceDelimiter}</strong>`}
      </Tooltip>
    )
  }
  return <>{display}</>
}

export default IdentifierString
