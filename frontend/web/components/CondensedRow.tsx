import { FC, PropsWithChildren } from 'react'

type CondensedColumnType = PropsWithChildren<{}>

const CondensedRow: FC<CondensedColumnType> = ({ children }) => {
  return (
    <div className='row'>
      <div className='col-xl-6 col-md-8'>{children}</div>
    </div>
  )
}

export default CondensedRow
