import { FC, HTMLAttributes } from 'react'
import cn from 'classnames'
import './BodyText.scss'

export type BodyTextSize = 'sm' | 'xs'
export type BodyTextWeight = 'medium' | 'semibold'

export type BodyTextProps = HTMLAttributes<HTMLElement> & {
  // Leave unset for the default 14px
  size?: BodyTextSize
  // Leave unset for regular
  weight?: BodyTextWeight
  // Secondary text colour
  muted?: boolean
  // A span instead of a paragraph, for text inside a row or a sentence
  inline?: boolean
}

const BodyText: FC<BodyTextProps> = ({
  className,
  inline = false,
  muted = false,
  size,
  weight,
  ...rest
}) => {
  const Tag = inline ? 'span' : 'p'
  return (
    <Tag
      {...rest}
      className={cn(
        'ds-body-text',
        size && `ds-body-text--${size}`,
        weight && `ds-body-text--${weight}`,
        { 'ds-body-text--muted': muted },
        className,
      )}
    />
  )
}

export default BodyText
