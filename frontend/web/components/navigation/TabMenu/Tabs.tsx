import React, { useCallback, useEffect, useRef, useState } from 'react'
import ModalHR from 'components/modals/ModalHR'
import Utils from 'common/utils/utils'
import { useHistory } from 'react-router-dom'
import TabButton from './TabButton'
import { IonIcon } from '@ionic/react'
import { ellipsisHorizontal } from 'ionicons/icons'
import Button from 'components/base/forms/Button'
import classNames from 'classnames'
import DropdownMenu from 'components/base/DropdownMenu'

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

  const moreMeasureRef = useRef<HTMLButtonElement | null>(null)
  const measureRefs = useRef<(HTMLAnchorElement | HTMLButtonElement | null)[]>(
    [],
  )
  const measureRef = useRef<HTMLDivElement | null>(null)

  const computeVisible = useCallback(() => {
    const nav = navRef.current
    const meas = measureRef.current
    if (!nav || !meas) return

    const cw = nav.clientWidth

    // right edges of each measured tab (includes gap/margins via offsetLeft)
    const rights = tabChildren.map((_, i) => {
      const el = measureRefs.current[i]
      return el ? el.offsetLeft + el.offsetWidth : 0
    })
    if (!rights.length) {
      setVisibleCount(0)
      return
    }

    const allRight = rights[rights.length - 1]
    if (allRight <= cw) {
      setVisibleCount(rights.length)
      return
    }

    const styles = getComputedStyle(
      meas.querySelector(':scope > div') as HTMLElement,
    )
    const gap = parseFloat(styles.columnGap || styles.gap || '0') || 0
    const moreW = moreMeasureRef.current?.offsetWidth || 0

    let vis = 0
    for (let i = 0; i < rights.length; i++) {
      if (rights[i] + gap + moreW <= cw) vis = i + 1
      else break
    }
    setVisibleCount(Math.max(1, vis))
  }, [tabChildren])

  useEffect(() => {
    if (!navRef.current) return

    computeVisible()
    const ro = new ResizeObserver(() => computeVisible())
    ro.observe(navRef.current)

    const onResize = () => computeVisible()
    window.addEventListener('resize', onResize)

    return () => {
      ro.disconnect()
      window.removeEventListener('resize', onResize)
    }
  }, [computeVisible, tabChildren.length])

  const registerMeasure = useCallback(
    (i: number) => (el: HTMLAnchorElement | HTMLButtonElement | null) => {
      measureRefs.current[i] = el
    },
    [],
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
  const isTabAllowedToGrow = visibleCount === tabChildren.length
  const handleChange = (
    e: React.MouseEvent<HTMLDivElement>,
    tabLabel: string,
    i: number,
  ) => {
    e.stopPropagation()
    e.preventDefault()
    if (urlParam) {
      const searchParams = new URLSearchParams(window.location.search)
      searchParams.set(
        urlParam,
        String(tabLabel).toLowerCase().replace(/ /g, '-'),
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
    <div className={`tabs ${className}`}>
      <div
        ref={measureRef}
        className={`${
          hideNav ? '' : 'tabs-nav'
        } ${theme} tabs-measure d-flex flex-nowrap align-items-center w-100`}
        aria-hidden
      >
        <div className='d-flex flex-nowrap align-items-center'>
          {tabChildren.map((child, i) => (
            <TabButton
              ref={registerMeasure(i)}
              key={`measure-${i}`}
              i={i}
              isSelected={false}
              noFocus
              buttonTheme={buttonTheme}
              onChange={() => {}}
              routerHistory={routerHistory}
              setInternalValue={() => {}}
              uncontrolled={false}
              child={child}
              className={isTabAllowedToGrow ? 'tab-nav-full' : ''}
            >
              {child.props.tabLabel}
            </TabButton>
          ))}
        </div>

        {/* right group: the "More" button, pushed to the end */}
        <div className='ms-auto d-flex align-items-center flex-shrink-0'>
          <Button
            ref={moreMeasureRef as any}
            style={{ borderRadius: 6, height: 34, width: 34 }}
            theme='secondary'
            className='d-flex align-items-center m-0 p-0'
          >
            <IonIcon className='fs-small' icon={ellipsisHorizontal} />
          </Button>
        </div>
      </div>
      <div
        ref={navRef}
        className={`${
          hideNav ? '' : 'tabs-nav'
        } ${theme} justify-content-between align-items-center`}
        style={{
          ...(isMobile ? { flexWrap: 'wrap' } : {}),
        }}
      >
        <div className='d-flex align-items-center  w-100'>
          {!hideNav &&
            tabChildren.map((child, i) => {
              const isSelected = value === i
              const hidden = i >= visibleCount
              if (!child || hidden) {
                return null
              }
              return (
                <TabButton
                  // buttonTheme={buttonTheme}
                  key={`button${i}`}
                  isSelected={isSelected}
                  className={isTabAllowedToGrow ? 'tab-nav-full' : ''}
                  noFocus={noFocus}
                  onChange={(e) =>
                    handleChange(
                      e,
                      String(
                        child.props.tabLabelString || child.props.tabLabel,
                      ),
                      i,
                    )
                  }
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
        {
          <div
            className='d-flex align-items-center justify-content-center'
            style={{
              backgroundColor: 'var(--bs-light300)',
              borderRadius: 6,
              height: 32,
              width: 32,
            }}
          >
            <DropdownMenu
              items={tabChildren.slice(visibleCount).map((child, i) => ({
                className: classNames('', [
                  value === i + visibleCount
                    ? 'text-primary fw-semibold bg-primary-opacity-5 fill-primary'
                    : 'hover-color-primary',
                ]),
                label: (
                  <div className='d-flex align-items-center text-nowrap tabs-nav full-width'>
                    <TabButton
                      buttonTheme={buttonTheme}
                      key={`button${i}`}
                      isSelected={false}
                      className={classNames(
                        'full-width btn-no-focus width-100',
                        [
                          value === i + visibleCount
                            ? 'text-primary fw-semibold fill-primary'
                            : 'hover-color-primary',
                        ],
                      )}
                      noFocus={noFocus}
                      routerHistory={routerHistory}
                      setInternalValue={setInternalValue}
                      uncontrolled={uncontrolled}
                      urlParam={urlParam}
                      child={child}
                      i={i}
                    >
                      {child.props.tabLabel}
                    </TabButton>
                  </div>
                ) as React.ReactNode,
                onClick: (e: React.MouseEvent<HTMLDivElement>) => {
                  handleChange(
                    e,
                    String(child.props.tabLabelString || child.props.tabLabel),
                    i + visibleCount,
                  )
                },
              }))}
            />
          </div>
        }
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
