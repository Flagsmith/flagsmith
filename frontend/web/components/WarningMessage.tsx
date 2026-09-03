import { FC, ReactNode } from 'react'
import Banner from './Banner'

type WarningMessageType = {
  warningMessage: ReactNode
  warningMessageClass?: string
}

const WarningMessage: FC<WarningMessageType> = ({
  warningMessage,
  warningMessageClass,
}) => {
  if (!warningMessage) {
    return null
  }

  return (
    <Banner variant='warning' className={warningMessageClass}>
      {warningMessage}
    </Banner>
  )
}

export default WarningMessage
