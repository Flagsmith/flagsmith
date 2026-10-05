import { FC, ThHTMLAttributes } from 'react'

// scope is what lets a screen reader read a cell with its column name.
const TableColumnHeader: FC<ThHTMLAttributes<HTMLTableCellElement>> = ({
  children,
  scope = 'col',
  ...rest
}) => (
  <th {...rest} scope={scope}>
    {children}
  </th>
)

export default TableColumnHeader
