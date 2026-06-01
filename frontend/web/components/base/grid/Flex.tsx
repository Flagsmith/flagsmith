import React, { FC } from 'react'

type FlexProps = React.HTMLAttributes<HTMLDivElement>

const Flex: FC<FlexProps> = ({ className, ...rest }) => (
  <div {...rest} className={`${className || ''} flex flex-1`} />
)

export default Flex
