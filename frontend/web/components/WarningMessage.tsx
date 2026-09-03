import { FC, ReactNode } from 'react'
import Banner from './Banner'

type WarningMessageType = {
  warningMessage: ReactNode
}

const WarningMessage: FC<WarningMessageType> = ({ warningMessage }) =>
  warningMessage ? <Banner variant='warning'>{warningMessage}</Banner> : null

export default WarningMessage
