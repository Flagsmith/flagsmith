import { FC, ReactNode } from 'react'
import Banner from 'components/Banner'

type SuccessMessageProps = {
  children?: ReactNode
  title?: string
}

const SuccessMessage: FC<SuccessMessageProps> = ({
  children,
  title = 'SUCCESS',
}) => (
  <Banner variant='success'>
    <div>
      <div className='fw-semibold'>{title}</div>
      {children}
    </div>
  </Banner>
)

export default SuccessMessage
