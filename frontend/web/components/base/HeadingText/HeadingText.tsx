import { FC, HTMLAttributes } from 'react'
import cn from 'classnames'
import './HeadingText.scss'

export type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6
export type HeadingSize = 'lg' | 'md' | 'sm'

export type HeadingTextProps = HTMLAttributes<HTMLHeadingElement> & {
  level: HeadingLevel
  // Leave unset to size by level
  size?: HeadingSize
}

const HeadingText: FC<HeadingTextProps> = ({
  className,
  level,
  size,
  ...rest
}) => {
  const Tag: `h${HeadingLevel}` = `h${level}`
  return (
    <Tag
      {...rest}
      className={cn(
        'ds-heading-text',
        size && `ds-heading-text--${size}`,
        className,
      )}
    />
  )
}

export default HeadingText
