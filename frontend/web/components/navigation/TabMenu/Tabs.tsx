import React, {
  ReactElement,
  ReactNode,
  useCallback,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import ModalHR from 'components/modals/ModalHR'
import Utils from 'common/utils/utils'
import { useHistory } from 'react-router-dom'
import TabButton from './TabButton'

import classNames from 'classnames'
import DropdownMenu from 'components/base/DropdownMenu'
import { useOverflowVisibleCount } from 'common/hooks/useOverflowVisibleCount'

interface TabsProps {
  children: ReactNode | ReactNode[]
  onChange?: (index: number) => void
  theme?: 'tab' | 'pill'
  value?: number
  className?: string
  /** @deprecated Use `useTabUrlSync(paramName, labels)` in the consumer and pass `value`/`onChange`. */
  urlParam?: string
  hideNavOnSingleTab?: boolean
  buttonTheme?: string
  noFocus?: boolean
  /** @deprecated Domain-specific class hook — push padding to the consuming `TabItem` via `className` instead. */
  isRoles?: boolean
  /** @deprecated `useTabUrlSync` handles the modal-portal Router fallback internally; this prop is only honoured by the legacy `urlParam` path. */
  history?: any
  cta?: ReactNode
}

// Falls back to tabLabel when it is already a plain string, so consumers
// only need tabLabelString when tabLabel is JSX.
const getLabelString = (child: ReactElement): string => {
  const { tabLabel, tabLabelString } = child.props as {
    tabLabel?: ReactNode
    tabLabelString?: string
  }
  if (tabLabelString) return tabLabelString
  return typeof tabLabel === 'string' ? tabLabel : ''
}

const toUrlSlug = (label: string): string =>
  label.toLowerCase().replace(/ /g, '-')

const Tabs: React.FC<TabsProps> = ({
  buttonTheme,
  children,
  className = '',
  cta,
  hideNavOnSingleTab,
  history,
  isRoles,
  noFocus,
  onChange,
  theme = 'tab',
  urlParam,
  value: propValue = 0,
}) => {
  const tabChildren = (Array.isArray(children) ? children : [children]).filter(
    Boolean,
  )
  const routerHistory = useHistory() || history

  const disableOverflow = theme === 'pill'
  let value = propValue
  if (urlParam) {
    const tabParam = Utils.fromParam()[urlParam]
    if (tabParam) {
      const idx = tabChildren.findIndex(
        (v) => v && toUrlSlug(getLabelString(v as ReactElement)) === tabParam,
      )
      if (idx !== -1) value = idx
    }
  }

  const hideNav = tabChildren.length === 1 && hideNavOnSingleTab

  const outerContainerRef = useRef<HTMLDivElement>(null)
  const itemsContainerRef = useRef<HTMLDivElement>(null)
  const overflowButtonRef = useRef<HTMLDivElement>(null)
  const [overflowButtonWidth, setOverflowButtonWidth] = useState(54) // fallback

  useLayoutEffect(() => {
    if (disableOverflow) return
    if (overflowButtonRef.current) {
      const width = overflowButtonRef.current.offsetWidth
      const marginLeft =
        parseInt(getComputedStyle(overflowButtonRef.current).marginLeft, 10) ||
        0
      setOverflowButtonWidth(width + marginLeft)
    }
  }, [disableOverflow])

  const { isMeasuring, visibleCount } = useOverflowVisibleCount({
    extraWidth: overflowButtonWidth,
    force: false,
    gap: 0,
    itemCount: tabChildren.length,
    itemsContainerRef,
    outerContainerRef,
  })

  const visible = useMemo(
    // Disable overflow for pill tabs
    () => (disableOverflow ? tabChildren : tabChildren.slice(0, visibleCount)),
    [tabChildren, visibleCount, disableOverflow],
  )
  const overflow = useMemo(
    () => (disableOverflow ? [] : tabChildren.slice(visibleCount)),
    [tabChildren, visibleCount, disableOverflow],
  )
  const canGrow = !isMeasuring && visibleCount === tabChildren.length

  const handleChange = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>, tabLabel: string, i: number) => {
      e.stopPropagation()
      e.preventDefault()
      if (urlParam) {
        const searchParams = new URLSearchParams(window.location.search)
        searchParams.set(urlParam, toUrlSlug(tabLabel))
        routerHistory?.replace({
          pathname: window.location.pathname,
          search: searchParams.toString(),
        })
      }
      onChange?.(i)
    },
    [onChange, routerHistory, urlParam],
  )

  return (
    <div className={`tabs ${className}`}>
      <div
        ref={outerContainerRef}
        className={`${
          hideNav ? '' : 'tabs-nav'
        } ${theme} justify-content-between gap-4 d-flex align-items-center`}
      >
        <div
          ref={itemsContainerRef}
          className={classNames('d-flex align-items-center flex-1', 'gap-2', {
            'opacity-0': isMeasuring,
          })}
        >
          {(isMeasuring ? tabChildren : visible).map((child, i) => {
            const isSelected = !isMeasuring && value === i
            return (
              <TabButton
                key={`button-${i}`}
                isSelected={isSelected}
                className={canGrow ? 'tab-nav-full' : ''}
                noFocus={noFocus}
                onClick={(e: React.MouseEvent<HTMLButtonElement>) =>
                  handleChange(e, getLabelString(child as ReactElement), i)
                }
                child={child}
                buttonTheme={buttonTheme}
              >
                {child.props.tabLabel}
              </TabButton>
            )
          })}
        </div>
        {overflow.length > 0 && !isMeasuring && (
          <div
            className='d-flex align-items-center justify-content-center ms-2 flex-shrink-0 btn btn-secondary'
            style={{
              backgroundColor: 'var(--bs-light300)',
              borderRadius: 6,
              height: 32,
              width: 32,
            }}
            data-test='tabs-overflow-button'
          >
            <DropdownMenu
              items={overflow.map((child, i) => {
                const actualIndex = i + visibleCount
                const active = value === actualIndex
                return {
                  className: classNames('', [
                    active
                      ? 'text-primary fw-semibold bg-primary-opacity-5 fill-primary'
                      : 'hover-color-primary',
                  ]),
                  label: (
                    <div className='d-flex align-items-center text-nowrap tabs-nav full-width'>
                      <TabButton
                        key={`overflow-${actualIndex}`}
                        isSelected={false}
                        className={classNames(
                          'full-width btn-no-focus width-100',
                          active && 'text-primary fw-semibold fill-primary',
                        )}
                        noFocus={noFocus}
                        child={child}
                        buttonTheme={buttonTheme}
                      >
                        {child.props.tabLabel}
                      </TabButton>
                    </div>
                  ) as React.ReactNode,
                  onClick: (e: any) => {
                    handleChange(
                      e,
                      getLabelString(child as ReactElement),
                      actualIndex,
                    )
                  },
                }
              })}
            />
          </div>
        )}
        {cta && <div className='flex-shrink-0'>{cta}</div>}
      </div>
      {theme === 'tab' && !hideNav && <ModalHR className='tab-nav-hr' />}
      <div className='tabs-content'>
        {tabChildren.map((child, i) => {
          const isSelected = value === i
          return (
            <div
              key={`content-${i}`}
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
