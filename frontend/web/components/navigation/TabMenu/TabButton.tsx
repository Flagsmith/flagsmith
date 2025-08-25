import React from 'react'
import { themeClassNames } from 'components/base/forms/Button'

import Button from 'components/base/forms/Button'

interface TabButtonProps {
  routerHistory: any
  setInternalValue: (value: number) => void
  uncontrolled: boolean
  urlParam?: string
  noFocus?: boolean
  isSelected: boolean
  onChange?: (e: React.MouseEvent<HTMLButtonElement>) => void
  buttonTheme?: string
  className?: string
  child: React.ReactElement
  i: number
  children: React.ReactNode
}

const TabButton = React.forwardRef<HTMLButtonElement | null, TabButtonProps>(
  (
    {
      buttonTheme,
      child,
      className,
      i,
      isSelected,
      noFocus,
      onChange,
      routerHistory,
      setInternalValue,
      uncontrolled,
      urlParam,
    },
    ref,
  ) => {
    return (
      <Button
        ref={ref as React.RefObject<HTMLButtonElement>}
        type='button'
        theme={buttonTheme as keyof typeof themeClassNames}
        data-test={child.props['data-test']}
        id={child.props.id}
        onClick={onChange}
        className={`btn-tab ${noFocus ? 'btn-no-focus' : ''} ${
          isSelected ? ' tab-active' : ''
        } ${className}`}
      >
        {child.props.tabLabel}
      </Button>
    )
  },
)

export default TabButton
