import { FC, ReactNode } from 'react'
import './DependenciesTable.scss'

type DependenciesTableProps = {
  head: ReactNode
  children: ReactNode
}

// The table shell both halves share. Columns are fixed, so a long feature name
// truncates in its cell rather than widening the table.
const DependenciesTable: FC<DependenciesTableProps> = ({ children, head }) => (
  <table className='dependencies-table'>
    <thead>
      <tr>{head}</tr>
    </thead>
    <tbody>{children}</tbody>
  </table>
)

export default DependenciesTable
