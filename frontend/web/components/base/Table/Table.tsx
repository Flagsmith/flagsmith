import { FC, ReactNode, TableHTMLAttributes } from 'react'
import cn from 'classnames'
import './Table.scss'

// Surface draws its own border and fills the header, which is what
// MetricsTable and ExperimentsTable do. Ghost draws neither, for a table
// inside a container that already has a border.
export type TableVariant = 'surface' | 'ghost'

// Fixed shares the width evenly and truncates long cells; auto lets content
// size the columns.
export type TableLayout = 'auto' | 'fixed'

export type TableProps = TableHTMLAttributes<HTMLTableElement> & {
  children: ReactNode
  variant?: TableVariant
  layout?: TableLayout
}

type Part = FC<{ children?: ReactNode; className?: string }>

const Table: FC<TableProps> & {
  Header: Part
  Body: Part
  Row: Part
  ColumnHeader: Part
  Cell: Part
} = ({
  children,
  className,
  layout = 'auto',
  variant = 'surface',
  ...rest
}) => (
  <table
    {...rest}
    className={cn(
      'ds-table',
      `ds-table--${variant}`,
      `ds-table--${layout}`,
      className,
    )}
  >
    {children}
  </table>
)

Table.Header = ({ children, className }) => (
  <thead className={className}>{children}</thead>
)

Table.Body = ({ children, className }) => (
  <tbody className={className}>{children}</tbody>
)

Table.Row = ({ children, className }) => (
  <tr className={className}>{children}</tr>
)

// scope is what lets a screen reader read a cell with its column name.
Table.ColumnHeader = ({ children, className }) => (
  <th scope='col' className={className}>
    {children}
  </th>
)

Table.Cell = ({ children, className }) => (
  <td className={className}>{children}</td>
)

Table.displayName = 'Table'
export default Table
