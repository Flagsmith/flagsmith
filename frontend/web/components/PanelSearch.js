import React, { Component } from 'react'
import { AutoSizer, List } from 'react-virtualized'
import Popover from './base/Popover'
import Input from './base/forms/Input'
import Icon from './Icon'
import classNames from 'classnames'
const PanelSearch = class extends Component {
  static displayName = 'PanelSearch'

  static propTypes = {
    actionButton: OptionalNode,
    filterElement: OptionalNode,
    filterRow: OptionalFunc,
    goToPage: OptionalFunc,
    isLoading: OptionalBool,
    items: propTypes.any,
    listClassName: OptionalString,
    nextPage: OptionalFunc,
    noResultsText: OptionalString,
    paging: OptionalObject,
    renderNoResults: propTypes.any,
    renderRow: RequiredFunc,
    search: OptionalString,
    searchPanel: OptionalNode,
    sorting: OptionalArray,
    title: propTypes.node,
  }

  constructor(props, context) {
    super(props, context)
    const defaultSortingOption = _.find(_.get(props, 'sorting', []), {
      default: true,
    })
    this.state = {
      sortBy: defaultSortingOption ? defaultSortingOption.value : null,
      sortOrder: defaultSortingOption ? defaultSortingOption.order : null,
    }
  }

  filter() {
    let search = this.props.search || this.state.search || ''
    if (this.state.exact) {
      search = search.replace(/^"+|"+$/g, '')
    }
    const filter = this.props.filter
    const { filterRow, items } = this.props
    if (filterRow && (search || filter)) {
      return this.sort(
        _.filter(items, (value, index) =>
          filterRow(value, search.toLowerCase(), index),
        ),
      )
    }
    return this.sort(items)
  }

  sort(items) {
    const { sortBy, sortOrder } = this.state
    if (sortBy) {
      return _.orderBy(items, [sortBy], [sortOrder])
    }

    return items
  }

  onSort(e, sortOption) {
    e.preventDefault()
    const { sortBy, sortOrder } = this.state
    if (sortOption.value === sortBy) {
      this.setState({ sortOrder: sortOrder === 'asc' ? 'desc' : 'asc' }, () => {
        if (this.props.onSortChange) {
          this.props.onSortChange({
            sortBy: this.state.sortBy,
            sortOrder: this.state.sortOrder,
          })
        }
      })
    } else {
      this.setState(
        { sortBy: sortOption.value, sortOrder: sortOption.order },
        () => {
          if (this.props.onSortChange) {
            this.props.onSortChange({
              sortBy: this.state.sortBy,
              sortOrder: this.state.sortOrder,
            })
          }
        },
      )
    }
  }

  renderContainer = (children) => {
    const renderRow = ({ index, key, style }) => {
      return (
        <div key={key} style={style}>
          {this.props.renderRow(children[index])}
        </div>
      )
    }
    if (children && children?.length > 100 && this.props.itemHeight) {
      return (
        <div>
          <AutoSizer disableHeight>
            {({ width }) => (
              <List
                style={{ overflowX: 'hidden' }}
                width={width}
                height={this.props.itemHeight * 10}
                rowCount={children.length}
                rowHeight={this.props.itemHeight}
                rowRenderer={renderRow}
              />
            )}
          </AutoSizer>
        </div>
      )
    }
    return children?.map(this.props.renderRow)
  }

  render() {
    const { sortBy, sortOrder } = this.state
    const {
      action,
      goToPage,
      isLoading,
      items,
      nextPage,
      paging,
      prevPage,
      renderNoResults,
      sorting,
    } = this.props
    const filteredItems = this.filter(items)
    const currentSort = _.find(sorting, { value: sortBy })

    let search = this.props.search || this.state.search || ''
    if (this.state.exact) {
      search = search.replace(/^"+|"+$/g, '')
    }
    return !search &&
      (!filteredItems || !filteredItems.length) &&
      !this.props.isLoading &&
      !this.props.renderSearchWithNoResults ? (
      renderNoResults || null
    ) : (
      <Panel
        className={this.props.className}
        title={this.props.title}
        action={
          this.props.filterRow ||
          this.props.sorting ||
          this.props.filterElement ||
          this.props.actionButton ? (
            <Row>
              {!!this.props.filterElement && this.props.filterElement}

              {!!this.props.sorting && (
                <Row className='mr-3 relative'>
                  <Popover
                    renderTitle={(toggle, isActive) => (
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
                    {(toggle) => (
                      <div className='popover-inner__content'>
                        {this.props.sorting.map((sortOption, i) => (
                          <a
                            key={i}
                            className='popover-bt__list-item'
                            href='#'
                            onClick={(e) => {
                              this.onSort(e, sortOption)
                              toggle()
                            }}
                          >
                            <Row space className='px-3 py-2'>
                              <div>{sortOption.label}</div>
                              {currentSort &&
                                currentSort.value === sortOption.value && (
                                  <div>
                                    <Icon
                                      name={
                                        sortOrder === 'asc'
                                          ? 'chevron-up'
                                          : 'chevron-down'
                                      }
                                    />
                                  </div>
                                )}
                            </Row>
                          </a>
                        ))}
                      </div>
                    )}
                  </Popover>
                </Row>
              )}
              {!!this.props.filterRow && (
                <Row>
                  {this.props.showExactFilter && (
                    <div style={{ width: 140 }}>
                      <Select
                        size='select-sm'
                        styles={{
                          control: (base) => ({
                            ...base,
                            '&:hover': { borderColor: '$bt-brand-secondary' },
                            border: '1px solid $bt-brand-secondary',
                            height: 30,
                          }),
                        }}
                        onChange={(v) => {
                          this.setState({ exact: v.label === 'Exact' })
                          if (this.props.search) {
                            this.props.onChange &&
                              this.props.onChange(
                                !this.state.exact
                                  ? `"${this.props.search}"`
                                  : this.props.search.replace(/^"+|"+$/g, ''),
                              )
                          }
                        }}
                        value={{
                          label: this.state.exact
                            ? 'Exact'
                            : this.props.filterLabel ||
                              (Utils.getIsEdge() ? 'Starts with' : 'Contains'),
                        }}
                        options={[
                          {
                            label: Utils.getIsEdge()
                              ? 'Starts with'
                              : 'Contains',
                            value: 'Contains',
                          },
                          {
                            label: 'Exact',
                            value: 'Exact',
                          },
                        ]}
                      />
                    </div>
                  )}
                  <Row onClick={() => this.input.focus()}>
                    <Input
                      ref={(c) => (this.input = c)}
                      onBlur={this.props.onBlur}
                      onChange={(e) => {
                        const v = Utils.safeParseEventValue(e)
                        this.props.onChange
                          ? this.props.onChange(this.state.exact ? `"${v}"` : v)
                          : this.setState({
                              search: Utils.safeParseEventValue(e),
                            })
                      }}
                      type='text'
                      value={search}
                      size='small'
                      placeholder='Search'
                      search
                    />
                  </Row>
                </Row>
              )}
              {!!this.props.actionButton && this.props.actionButton}
            </Row>
          ) : (
            action || null
          )
        }
      >
        {this.props.searchPanel}
        <div
          id={this.props.id}
          className={classNames('search-list', this.props.listClassName)}
          style={isLoading ? { opacity: 0.5 } : {}}
        >
          {this.props.header}

          {this.props.isLoading && (!filteredItems || !items) ? (
            <div className='text-center'>
              <Loader />
            </div>
          ) : filteredItems && filteredItems.length ? (
            this.renderContainer(filteredItems)
          ) : renderNoResults && !search ? (
            renderNoResults
          ) : (
            <Row className='list-item'>
              {!isLoading && (
                <>
                  {this.props.noResultsText?.(search) || (
                    <div className='table-column'>
                      {'No results '}
                      {search && (
                        <span>
                          for
                          <strong>{` "${search}"`}</strong>
                        </span>
                      )}
                    </div>
                  )}
                </>
              )}
            </Row>
          )}
          {!!paging && (
            <Paging
              paging={paging}
              isLoading={isLoading}
              nextPage={nextPage}
              prevPage={prevPage}
              goToPage={goToPage}
            />
          )}
          {this.props.renderFooter && (
            <footer className='panel-footer'>
              {this.props.renderFooter()}
            </footer>
          )}
        </div>
      </Panel>
    )
  }
}
export default PanelSearch
