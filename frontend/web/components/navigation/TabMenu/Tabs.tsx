import React, {
  isValidElement,
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
import { TabItemProps } from './TabItem'
import TabLabel from './TabLabel'

import classNames from 'classnames'
import DropdownMenu, { DropdownMenuItem } from 'components/base/DropdownMenu'
import IconButton from 'components/base/IconButton'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import { useOverflowVisibleCount } from 'common/hooks/useOverflowVisibleCount'
import { useBreakpoint } from 'common/hooks/useBreakpoint'

interface TabsProps {
  children: ReactNode | ReactNode[]
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
  cta?: ReactNode
}

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
  uncontrolled = false,
  urlParam,
  value: propValue = 0,
}) => {
  const tabChildren = (Array.isArray(children) ? children : [children]).filter(
    (child): child is ReactElement<TabItemProps> => isValidElement(child),
  )
  const [internalValue, setInternalValue] = useState(0)
  const routerHistory = useHistory() || history

  const disableOverflow = theme === 'pill'
  let value = uncontrolled ? internalValue : propValue
  if (urlParam) {
    const tabParam = Utils.fromParam()[urlParam]
    if (tabParam) {
      const idx = tabChildren.findIndex(
        (v) =>
          String(v?.props?.tabLabelString || v?.props?.tabLabel)
            .toLowerCase()
            .replace(/ /g, '-') === tabParam,
      )
      if (idx !== -1) value = idx
    }
  }

  const hideNav = tabChildren.length === 1 && hideNavOnSingleTab

  const outerContainerRef = useRef<HTMLDivElement>(null)
  const itemsContainerRef = useRef<HTMLDivElement>(null)
  const overflowButtonRef = useRef<HTMLDivElement>(null)
  const [overflowButtonWidth, setOverflowButtonWidth] = useState(54) // fallback
  const isPhone = useBreakpoint('isPhone')

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
  const hasOverflow = overflow.length > 0 && !isMeasuring
  const activeTab = tabChildren[value]
  const tabLabelOf = (child: ReactElement<TabItemProps>) =>
    String(child.props.tabLabelString || child.props.tabLabel)

  const handleChange = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>, tabLabel: string, i: number) => {
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
    },
    [onChange, routerHistory, uncontrolled, urlParam],
  )

  return (
    <div className={`tabs ${className}`}>
      <div
        ref={outerContainerRef}
        className={`${
          hideNav ? '' : 'tabs-nav'
        } ${theme} justify-content-between gap-4 d-flex align-items-center ${className}`}
      >
        <div
          ref={itemsContainerRef}
          className={classNames(
            'align-items-center flex-1 gap-2',
            hasOverflow ? 'd-none d-md-flex' : 'd-flex',
            { 'opacity-0': isMeasuring },
          )}
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
                  handleChange(
                    e,
                    String(child.props.tabLabelString || child.props.tabLabel),
                    i,
                  )
                }
                child={child}
                buttonTheme={buttonTheme}
              >
                {child.props.tabLabel}
              </TabButton>
            )
          })}
        </div>
        {hasOverflow && activeTab && (
          <DropdownMenu
            aria-label='Sections'
            trigger={
              isPhone ? (
                // Tabs don't fit on phones, so the trigger shows the current section
                <BareButton className='d-flex align-items-center justify-content-between gap-2 w-100 px-0 py-2 text-start'>
                  <span className='h5 mb-0 text-truncate'>
                    {activeTab.props.tabLabel}
                  </span>
                  <Icon name='chevron-down' width={18} />
                </BareButton>
              ) : (
                <IconButton
                  className='ms-2 flex-shrink-0'
                  variant='secondary'
                  size='small'
                  aria-label='More tabs'
                >
                  <Icon name='more-vertical' width={18} />
                </IconButton>
              )
            }
          >
            {(isPhone ? tabChildren : overflow).map((child) => {
              const i = tabChildren.indexOf(child)
              return (
                <DropdownMenuItem
                  key={`menu-${i}`}
                  current={value === i}
                  onSelect={(e) => handleChange(e, tabLabelOf(child), i)}
                >
                  <TabLabel
                    tabLabel={child.props.tabLabel}
                    isDirty={child.props.isDirty}
                  />
                </DropdownMenuItem>
              )
            })}
          </DropdownMenu>
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
