import React, {
  ReactElement,
  ReactNode,
  useCallback,
  useMemo,
  useRef,
  useState,
  ChangeEvent,
  CSSProperties,
} from 'react'
import { AutoSizer, List } from 'react-virtualized'
import Popover from './base/Popover'
import Input from './base/forms/Input'
import Icon from './Icon'
import classNames from 'classnames'
import { IonIcon } from '@ionic/react'
import { chevronDown, chevronUp } from 'ionicons/icons'
import Button from './base/forms/Button'
import Paging from './Paging'
import _ from 'lodash'
import Panel from './base/grid/Panel'
import Utils from 'common/utils/utils'

export type SortOption = {
  value: string
  order: 'asc' | 'desc'
  default?: boolean
  label: string
}

export interface PanelSearchProps<T> {
  actionButton?: ReactNode
  filterElement?: ReactNode
  filterRow?: (item: T, search: string, index: number) => boolean
  goToPage?: (page: number) => void
  isLoading?: boolean
  items: T[] | undefined | null
  listClassName?: string
  nextPage?: () => void
  noResultsText?: (search?: string) => ReactNode
  onRefresh?: () => void
  paging?: any
  renderNoResults?: ReactNode
  renderRow: (item: T, index: number) => ReactNode
  search?: string | undefined | null
  searchPanel?: ReactNode
  sorting?: SortOption[]
  title?: ReactNode
  filterRowContent?: ReactNode
  onBlur?: () => void
  onChange?: (value: string) => void
  id?: string
  header?: ReactNode
  renderFooter?: () => ReactNode
  renderSearchWithNoResults?: boolean
  className?: string
  onSortChange?: (args: {
    sortBy: string | null
    sortOrder: 'asc' | 'desc' | null
  }) => void
  itemHeight?: number
  action?: ReactNode
  prevPage?: () => void
  filter?: string
}

const PanelSearch = <T,>(props: PanelSearchProps<T>): ReactElement => {
  const {
    action,
    filter,
    filterRow,
    isLoading,
    items,
    nextPage,
    onRefresh,
    onSortChange,
    paging,
    prevPage,
    renderNoResults,
    search: propSearch,
    sorting,
  } = props

  const defaultSortingOption = useMemo(() => {
    return sorting
      ? (_.find(sorting, { default: true }) as SortOption | undefined)
      : undefined
  }, [sorting])

  const [sortBy, setSortBy] = useState<string | null>(
    defaultSortingOption ? defaultSortingOption.value : null,
  )
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | null>(
    defaultSortingOption ? defaultSortingOption.order : null,
  )
  const [internalSearch, setInternalSearch] = useState<string>('')

  const exact = false

  const inputRef = useRef<any>(null)

  const sortItems = useCallback(
    (itemsToSort: T[]): T[] => {
      if (sortBy) {
        return _.orderBy(itemsToSort, [sortBy], [sortOrder || 'asc'])
      }
      return itemsToSort
    },
    [sortBy, sortOrder],
  )

  const filterItems = useCallback((): T[] => {
    let search = propSearch || internalSearch || ''
    if (exact) {
      search = search.replace(/^"+|"+$/g, '')
    }
    if (filterRow && (search || filter)) {
      const filtered = _.filter(items, (item, index) =>
        filterRow(item, search.toLowerCase(), index),
      )
      return sortItems(filtered)
    }
    return sortItems(items || [])
  }, [propSearch, internalSearch, exact, filter, filterRow, items, sortItems])

  const handleSort = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>, sortOption: SortOption) => {
      e.preventDefault()
      if (sortOption.value === sortBy) {
        const newSortOrder = sortOrder === 'asc' ? 'desc' : 'asc'
        setSortOrder(newSortOrder)
        onSortChange && onSortChange({ sortBy, sortOrder: newSortOrder })
      } else {
        setSortBy(sortOption.value)
        setSortOrder(sortOption.order)
        onSortChange &&
          onSortChange({
            sortBy: sortOption.value,
            sortOrder: sortOption.order,
          })
      }
    },
    [sortBy, sortOrder, onSortChange],
  )

  const renderContainer = useCallback(
    (children: T[]): ReactNode => {
      const rowRenderer = ({
        index,
        key,
        style,
      }: {
        index: number
        key: string
        style: CSSProperties
      }): ReactNode => (
        <div key={key} style={style}>
          {props.renderRow(children[index], index)}
        </div>
      )

      if (children.length > 100 && props.itemHeight) {
        return (
          <div>
            <AutoSizer disableHeight>
              {({ width }) => (
                <List
                  style={{ overflowX: 'hidden' }}
                  width={width}
                  height={props.itemHeight! * 10}
                  rowCount={children.length}
                  rowHeight={props.itemHeight!}
                  rowRenderer={rowRenderer}
                />
              )}
            </AutoSizer>
          </div>
        )
      }
      return children.map((item, index) => props.renderRow(item, index))
    },
    [props],
  )

  const filteredItems = filterItems()

  const currentSort: SortOption | undefined = useMemo(() => {
    return sorting ? _.find(sorting, (v) => v.value === sortBy) : undefined
  }, [sorting, sortBy])

  let search = propSearch || internalSearch || ''
  if (exact) {
    search = search.replace(/^"+|"+$/g, '')
  }

  if (
    !search &&
    (!filteredItems || filteredItems.length === 0) &&
    !isLoading &&
    !props.renderSearchWithNoResults
  ) {
    return <>{renderNoResults || null}</>
  }

  return (
    <Panel
      className={props.className}
      title={props.title}
      action={
        filterRow || sorting || props.filterElement || props.actionButton ? (
          <Row>
            {props.filterElement && props.filterElement}

            {sorting && (
              <Row className='mr-3 relative'>
                <Popover
                  renderTitle={(toggle: () => void, isActive: boolean) => (
                    <a
                      onClick={toggle}
                      className='flex-row'
                      style={{ color: isActive ? '#6837FC' : '#656d7b' }}
                    >
                      <span className='mr-1'>
                        <Icon
                          name='height'
                          fill={isActive ? '#6837FC' : '#656d7b'}
                        />
                      </span>
                      {currentSort ? currentSort.label : 'Unsorted'}
                    </a>
                  )}
                >
                  {(toggle: () => void) => (
                    <div>
                      {sorting.map((sortOption, i) => (
                        <a
                          key={i}
                          className='table-filter-item'
                          href='#'
                          onClick={(e) => {
                            handleSort(e, sortOption)
                            toggle()
                          }}
                        >
                          <Row space className='px-3 align-items-center py-2'>
                            <div>{sortOption.label}</div>
                            {currentSort?.value === sortOption.value && (
                              <IonIcon
                                icon={
                                  sortOrder === 'asc' ? chevronUp : chevronDown
                                }
                              />
                            )}
                          </Row>
                        </a>
                      ))}
                    </div>
                  )}
                </Popover>
              </Row>
            )}
            {onRefresh && (
              <Button theme='text' size='xSmall' onClick={onRefresh}>
                <Icon name='refresh' fill='#6837FC' width={16} /> Refresh
              </Button>
            )}
            {filterRow && (
              <Row>
                <Row
                  onClick={() => inputRef.current && inputRef.current.focus()}
                >
                  <Input
                    ref={inputRef}
                    onBlur={props.onBlur}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => {
                      const v = Utils.safeParseEventValue(e)
                      if (props.onChange) {
                        props.onChange(exact ? `"${v}"` : v)
                      } else {
                        setInternalSearch(Utils.safeParseEventValue(e))
                      }
                    }}
                    type='text'
                    value={search}
                    size='small'
                    placeholder='Search'
                    search
                  />
                  {props.filterRowContent}
                </Row>
              </Row>
            )}
            {props.actionButton && props.actionButton}
          </Row>
        ) : (
          action || null
        )
      }
    >
      {props.searchPanel}
      <div
        id={props.id}
        className={classNames('search-list', props.listClassName)}
        style={isLoading ? { opacity: 0.5 } : {}}
      >
        {props.header}
        {isLoading && (!filteredItems || !items) ? (
          <div className='text-center'>
            <Loader />
          </div>
        ) : filteredItems && filteredItems.length ? (
          renderContainer(filteredItems)
        ) : renderNoResults && !search ? (
          renderNoResults
        ) : (
          <Row className='list-item'>
            {!isLoading && (
              <>
                {props.noResultsText ? (
                  props.noResultsText(search) || (
                    <div className='table-column'>
                      No results{' '}
                      {search && (
                        <span>
                          for <strong>{` "${search}"`}</strong>
                        </span>
                      )}
                    </div>
                  )
                ) : (
                  <div className='table-column'>
                    No results{' '}
                    {search && (
                      <span>
                        for <strong>{` "${search}"`}</strong>
                      </span>
                    )}
                  </div>
                )}
              </>
            )}
          </Row>
        )}
        {paging && (
          <Paging
            paging={paging}
            isLoading={isLoading}
            nextPage={nextPage}
            prevPage={prevPage}
            goToPage={props.goToPage}
          />
        )}
        {props.renderFooter && (
          <footer className='panel-footer'>{props.renderFooter()}</footer>
        )}
      </div>
    </Panel>
  )
}

export default PanelSearch
