import {
  FC,
  HTMLAttributes,
  TableHTMLAttributes,
  TdHTMLAttributes,
  ThHTMLAttributes,
} from 'react'
import cn from 'classnames'
import './Table.scss'

export type TableVariant = 'surface' | 'ghost'

export type TableLayout = 'auto' | 'fixed'

// What the row is: `added` plays the enter and a fading tint, `editor` holds a
// control rather than data.
export type TableRowState = 'added' | 'editor'

export type TableRowProps = HTMLAttributes<HTMLTableRowElement> & {
  state?: TableRowState
  // What is happening to it, so either kind of row can be mid-write.
  pending?: boolean
}

export type TableProps = TableHTMLAttributes<HTMLTableElement> & {
  variant?: TableVariant
  layout?: TableLayout
  // Rows take a hover fill, for tracking one across its columns. A clickable
  // row needs .cursor-pointer as well.
  hover?: boolean
}

// Every part takes its element's own attributes, so a row can be clickable and
// a cell can span columns without dropping back to bare markup.
const Table: FC<TableProps> & {
  Header: FC<HTMLAttributes<HTMLTableSectionElement>>
  Body: FC<HTMLAttributes<HTMLTableSectionElement>>
  Row: FC<TableRowProps>
  ColumnHeader: FC<ThHTMLAttributes<HTMLTableCellElement>>
  Cell: FC<TdHTMLAttributes<HTMLTableCellElement>>
} = ({
  children,
  className,
  hover,
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
      { 'ds-table--hover': hover },
      className,
    )}
  >
    {children}
  </table>
)

Table.Header = ({ children, ...rest }) => <thead {...rest}>{children}</thead>
Table.Body = ({ children, ...rest }) => <tbody {...rest}>{children}</tbody>
Table.Row = ({ children, className, pending, state, ...rest }) => (
  <tr
    {...rest}
    className={cn(className, {
      'ds-table__row--pending': pending,
      [`ds-table__row--${state}`]: state,
    })}
  >
    {children}
  </tr>
)

// scope is what lets a screen reader read a cell with its column name.
Table.ColumnHeader = ({ children, scope = 'col', ...rest }) => (
  <th {...rest} scope={scope}>
    {children}
  </th>
)

Table.Cell = ({ children, ...rest }) => <td {...rest}>{children}</td>

Table.displayName = 'Table'
Table.Header.displayName = 'Table.Header'
Table.Body.displayName = 'Table.Body'
Table.Row.displayName = 'Table.Row'
Table.ColumnHeader.displayName = 'Table.ColumnHeader'
Table.Cell.displayName = 'Table.Cell'

export default Table
