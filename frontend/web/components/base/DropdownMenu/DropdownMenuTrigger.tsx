import { cloneElement, FC, ReactElement, Ref } from 'react'
import { useMergeRefs } from '@floating-ui/react'
import { PopoverTriggerProps } from 'components/base/Popover'

type TriggerProps = Record<string, unknown> & { ref?: Ref<Element> }

type DropdownMenuTriggerProps = {
  children: ReactElement<TriggerProps>
  popoverProps: PopoverTriggerProps
}

// Gives the trigger the popover's props without dropping its own handlers
// or ref: both run, the trigger's first
const DropdownMenuTrigger: FC<DropdownMenuTriggerProps> = ({
  children,
  popoverProps,
}) => {
  const own = children.props
  const ref = useMergeRefs([popoverProps.ref, own.ref])
  const props = Object.fromEntries(
    Object.entries(popoverProps).map(([key, value]) => {
      const ownValue = own[key]
      if (typeof value !== 'function' || typeof ownValue !== 'function') {
        return [key, value]
      }
      return [
        key,
        (...args: unknown[]) => {
          ownValue(...args)
          value(...args)
        },
      ]
    }),
  )
  return cloneElement(children, { ...props, ref })
}

export default DropdownMenuTrigger
