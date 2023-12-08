import React, { FC, useState } from 'react'
import TableFilter from './TableFilter'

type TableFilterType = {}

const TableSortFilter: FC<TableFilterType> = ({ title }) => {
  const [open, setOpen] = useState(false)

  return (
    <>
      <TableFilter title={'Sort'}></TableFilter>
    </>
  )
}

export default TableSortFilter
