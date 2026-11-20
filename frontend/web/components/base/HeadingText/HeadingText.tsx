import { FC, HTMLAttributes } from 'react'
import cn from 'classnames'
import { getHeadingSize, HeadingLevel } from './headingSize'
import './HeadingText.scss'

export type HeadingTextProps = HTMLAttributes<HTMLHeadingElement> & {
  // The level is both the tag and the size, so a heading can't look like
  // another level.
  level: HeadingLevel
}

const TAGS = {
  1: 'h1',
  2: 'h2',
  3: 'h3',
  4: 'h4',
  5: 'h5',
  6: 'h6',
} as const

const HeadingText: FC<HeadingTextProps> = ({ className, level, ...rest }) => {
  const Tag = TAGS[level]
  return (
    <Tag
      {...rest}
      className={cn(
        'ds-heading-text',
        `ds-heading-text--${getHeadingSize(level)}`,
        className,
      )}
    />
  )
}

export default HeadingText
