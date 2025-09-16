import React from 'react'
import { themeClassNames } from 'components/base/forms/Button'

import Button from 'components/base/forms/Button'

interface TabButtonProps {
  noFocus?: boolean
  isSelected: boolean
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void
  buttonTheme?: string
  className?: string
  child: React.ReactElement
  children: React.ReactNode
}

const TabButton = React.forwardRef<HTMLButtonElement | null, TabButtonProps>(
  ({ buttonTheme, child, className, isSelected, noFocus, onClick }, ref) => {
    return (
      <Button
        ref={ref as React.RefObject<HTMLButtonElement>}
        type='button'
        theme={buttonTheme as keyof typeof themeClassNames}
        data-test={child.props['data-test']}
        id={child.props.id}
        onClick={(e) => onClick?.(e)}
        className={`btn-tab px-2 ${noFocus ? 'btn-no-focus' : ''} ${
          isSelected ? ' tab-active' : ''
        } ${className}`}
      >
        {child.props.tabLabel}
      </Button>
    )
  },
)

export default TabButton
