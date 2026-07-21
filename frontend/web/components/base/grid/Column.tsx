import React, { FC } from 'react'

type ColumnProps = React.HTMLAttributes<HTMLDivElement>

const Column: FC<ColumnProps> = ({ className, ...rest }) => (
  <div {...rest} className={`${className || ''} flex-column`} />
)

export default Column
