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
  onChange?: (value: number) => void
  buttonTheme?: string
  child: React.ReactElement
  i: number
  children: React.ReactNode
}

const TabButton = React.forwardRef<HTMLButtonElement, TabButtonProps>(
  (
    {
      buttonTheme,
      child,
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
    const onClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      e.stopPropagation()
      e.preventDefault()
      if (urlParam) {
        const searchParams = new URLSearchParams(window.location.search)
        searchParams.set(
          urlParam,
          String(child.props.tabLabelString || child.props.tabLabel)
            .toLowerCase()
            .replace(/ /g, '-'),
        )
        routerHistory?.replace({
          pathname: window.location.pathname,
          search: searchParams.toString(),
        })
      } else if (uncontrolled) {
        setInternalValue(i)
      }
      onChange?.(i)
    }

    return (
      <Button
        ref={ref as React.RefObject<HTMLButtonElement>}
        type='button'
        theme={buttonTheme as keyof typeof themeClassNames}
        data-test={child.props['data-test']}
        id={child.props.id}
        onClick={onClick}
        className={`btn-tab ${noFocus ? 'btn-no-focus' : ''} ${
          isSelected ? ' tab-active' : ''
        }`}
      >
        {child.props.tabLabel}
      </Button>
    )
  },
)

export default TabButton
