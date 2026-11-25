import { FC, ReactNode } from 'react'
import { useCloseDropdownMenu } from './DropdownMenuContext'

type DropdownMenuRowProps = {
  // Content that is its own control, such as a nav link
  children: ReactNode
}

// The click comes from the link inside, which handles the keyboard itself
const DropdownMenuRow: FC<DropdownMenuRowProps> = ({ children }) => {
  const close = useCloseDropdownMenu()
  return (
    <div className='ds-dropdown-menu__row' onClick={close}>
      {children}
    </div>
  )
}

export default DropdownMenuRow
