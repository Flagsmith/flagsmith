import React, { useState } from 'react'
import ModalHR from 'components/modals/ModalHR'
import Utils from 'common/utils/utils'
import Button, { themeClassNames } from './Button'
import { useHistory, useLocation } from 'react-router-dom'

interface TabItemProps {
  tabLabel: React.ReactNode
  tabLabelString?: string
  'data-test'?: string
  id?: string
  className?: string
  children: React.ReactNode
}

interface TabsProps {
  children:
    | React.ReactElement<TabItemProps>
    | React.ReactElement<TabItemProps>[]
  onChange?: (index: number) => void
  theme?: 'tab' | 'pill'
  uncontrolled?: boolean
  value?: number
  className?: string
  urlParam?: string
  hideNavOnSingleTab?: boolean
  buttonTheme?: string
  noFocus?: boolean
  isRoles?: boolean
  history?: any
}

const Tabs: React.FC<TabsProps> = ({
  buttonTheme,
  children,
  className = '',
  hideNavOnSingleTab,
  history,
  isRoles,
  noFocus,
  onChange,
  theme = 'tab',
  uncontrolled = false,
  urlParam,
  value: propValue = 0,
}) => {
  const [internalValue, setInternalValue] = useState(0)
  const routerHistory = useHistory() || history
  const tabChildren = (Array.isArray(children) ? children : [children]).filter(
    Boolean,
  )
  let value = uncontrolled ? internalValue : propValue

  if (urlParam) {
    const tabParam = Utils.fromParam()[urlParam]
    if (tabParam) {
      const tab = tabChildren.findIndex((v) => {
        return (
          String(v?.props?.tabLabelString || v?.props?.tabLabel)
            .toLowerCase()
            .replace(/ /g, '-') === tabParam
        )
      })
      if (tab !== -1) {
        value = tab
      }
    }
  }

  const hideNav = tabChildren.length === 1 && hideNavOnSingleTab

  return (
    <div className={`tabs ${className}`}>
      <div
        className={`${hideNav ? '' : 'tabs-nav'} ${theme}`}
        style={isMobile ? { flexWrap: 'wrap' } : {}}
      >
        {!hideNav &&
          tabChildren.map((child, i) => {
            const isSelected = value === i
            if (!child) {
              return null
            }
            return (
              <Button
                type='button'
                theme={buttonTheme as keyof typeof themeClassNames}
                data-test={child.props['data-test']}
                id={child.props.id}
                key={`button${i}`}
                onClick={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  if (urlParam) {
                    const searchParams = new URLSearchParams(
                      window.location.search,
                    )
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
                }}
                className={`btn-tab ${noFocus ? 'btn-no-focus' : ''} ${
                  isSelected ? ' tab-active' : ''
                }`}
              >
                {child.props.tabLabel}
              </Button>
            )
          })}
      </div>
      {theme === 'tab' && !hideNav && <ModalHR className='tab-nav-hr' />}
      <div className='tabs-content'>
        {tabChildren.map((child, i) => {
          const isSelected = value === i
          return (
            <div
              key={`content${i}`}
              className={`tab-item ${isSelected ? ' tab-active' : ''} ${
                isRoles && 'p-0'
              } ${child.props.className || ''}`}
            >
              {child}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Tabs

// Example Usage
//   <Tabs value={tab} onChange={selectTab}>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 1 content</h2>
//     </TabItem>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 2 content</h2>
//     </TabItem>
//   </Tabs>
