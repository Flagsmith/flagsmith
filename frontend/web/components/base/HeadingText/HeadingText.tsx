import { FC, HTMLAttributes } from 'react'
import cn from 'classnames'
import './HeadingText.scss'

export type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6

export type HeadingTextProps = HTMLAttributes<HTMLHeadingElement> & {
  level: HeadingLevel
}

const HeadingText: FC<HeadingTextProps> = ({ className, level, ...rest }) => {
  const Tag: `h${HeadingLevel}` = `h${level}`
  return <Tag {...rest} className={cn('ds-heading-text', className)} />
}

export default HeadingText
