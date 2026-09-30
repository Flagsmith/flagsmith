import React, { HTMLAttributes } from 'react'
import cn from 'classnames'
import './Text.scss'

export type HeadingVariant = 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
export type BodyVariant = 'b1' | 'b2' | 'b3' | 'b4'
export type TextVariant = HeadingVariant | BodyVariant
export type TextWeight = 'regular' | 'medium' | 'semibold' | 'bold'
export type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6
export type BodyElement = 'p' | 'span' | 'div' | 'label' | 'legend'

type CommonProps = HTMLAttributes<HTMLElement> & {
  // Overrides the weight the variant carries. Closed set, so it still resolves
  // to a token rather than an arbitrary number.
  weight?: TextWeight
  className?: string
  children?: React.ReactNode
}

export type TextProps = CommonProps &
  (
    | {
        variant: HeadingVariant
        // Where this sits in the document outline, which is separate from how
        // big it looks. Required so the tag can't silently follow the variant.
        level: HeadingLevel
        as?: never
      }
    | {
        variant: BodyVariant
        as?: BodyElement
        level?: never
      }
  )

const isHeading = (variant: TextVariant): variant is HeadingVariant =>
  variant.startsWith('h')

const Text = ({
  as,
  children,
  className,
  level,
  variant,
  weight,
  ...rest
}: TextProps) => {
  // span by default: it adds no margin, so wrapping existing text doesn't move
  // anything. Callers ask for p or div when they want block flow.
  const Element = (isHeading(variant) ? `h${level}` : as ?? 'span') as 'span'

  return (
    <Element
      className={cn(
        'ds-text',
        `ds-text--${variant}`,
        weight && `ds-text--weight-${weight}`,
        className,
      )}
      {...rest}
    >
      {children}
    </Element>
  )
}

export default Text
