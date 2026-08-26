import { ComponentPropsWithoutRef, FC } from 'react'
import classNames from 'classnames'
import { getDefaultVariantKey } from 'common/utils/multivariate'

interface VariantKeyProps
  extends Omit<ComponentPropsWithoutRef<'span'>, 'children'> {
  // The variant's own key, absent when the user never set one.
  value?: string | null
  index: number
}

// A variant key is an identifier the SDKs match on, so it is set in mono to
// read as code rather than prose.
export const VariantKey: FC<VariantKeyProps> = ({
  className,
  index,
  value,
  ...rest
}) => (
  <span className={classNames('font-monospace', className)} {...rest}>
    {value || getDefaultVariantKey(index)}
  </span>
)
