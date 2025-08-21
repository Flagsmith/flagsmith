import React, { useCallback, useRef, useState } from 'react'
import ModalHR from 'components/modals/ModalHR'
import Utils from 'common/utils/utils'
import { useHistory } from 'react-router-dom'
import TabButton from './TabButton'

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
  overflowX?: boolean
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
  overflowX = false,
  theme = 'tab',
  uncontrolled = false,
  urlParam,
  value: propValue = 0,
}) => {
  const tabChildren = (Array.isArray(children) ? children : [children]).filter(
    Boolean,
  )
  const [internalValue, setInternalValue] = useState(0)
  const routerHistory = useHistory() || history
  const [visibleCount, setVisibleCount] = useState(tabChildren.length)

  const navRef = useRef<HTMLDivElement | null>(null)
  // We need to measure the parent width against the tab widths to see how many we can fit
  const tabRefs = useRef<(HTMLAnchorElement | HTMLButtonElement | null)[]>(
    Array(tabChildren.length).fill(null),
  )

  const registerTab = useCallback(
    (i: number) => (el: HTMLAnchorElement | HTMLButtonElement | null) => {
      tabRefs.current[i] = el
    },
    [],
  )

  const computeVisible = useCallback(() => {
    const container = navRef.current
    if (!container) return
    const cw = container.clientWidth
    let used = 0
    let vis = 0
    for (let i = 0; i < tabRefs.current.length; i++) {
      const el = tabRefs.current[i]
      if (!el) {
        vis++
        continue
      } // if not mounted yet, optimistically include
      const w = Math.ceil(el.getBoundingClientRect().width)
      if (used + w <= cw) {
        used += w
        vis++
      } else break
    }
    setVisibleCount(vis)
  }, [])

  React.useEffect(() => {
    // run after first paint and when tab count changes
    computeVisible()
  }, [computeVisible, tabChildren.length])

  React.useEffect(() => {
    if (!navRef.current) return
    const ro = new ResizeObserver(() => computeVisible())
    ro.observe(navRef.current)
    return () => ro.disconnect()
  }, [computeVisible])

  let value = uncontrolled ? internalValue : propValue
  console.log(visibleCount)
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
  const isCodeReferencesEnabled = Utils.getFlagsmithHasFeature(
    'git_code_references',
  )

  return (
    <div className={`tabs ${className}`}>
      <div
        ref={navRef}
        className={`${hideNav ? '' : 'tabs-nav'} ${theme}`}
        style={{
          // ...(overflowX && isCodeReferencesEnabled
          //   ? { overflowX: 'scroll' }
          //   : {}),
          ...(isMobile ? { flexWrap: 'wrap' } : {}),
        }}
      >
        {!hideNav &&
          tabChildren.map((child, i) => {
            const isSelected = value === i
            if (!child) {
              return null
            }
            return (
              <TabButton
                ref={registerTab(i)}
                buttonTheme={buttonTheme}
                key={`button${i}`}
                isSelected={isSelected}
                noFocus={noFocus}
                onChange={onChange}
                routerHistory={routerHistory}
                setInternalValue={setInternalValue}
                uncontrolled={uncontrolled}
                urlParam={urlParam}
                child={child}
                i={i}
              >
                {child.props.tabLabel}
              </TabButton>
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
