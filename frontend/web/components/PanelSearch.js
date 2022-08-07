import React, { Component } from 'react';
import { FixedSizeList as List } from 'react-window';
import Popover from './base/Popover';

const PanelSearch = class extends Component {
    static displayName = 'PanelSearch'

    static propTypes = {
        title: propTypes.node,
        items: propTypes.any,
        search: OptionalString,
        searchPanel: OptionalNode,
        renderRow: RequiredFunc,
        renderNoResults: propTypes.any,
        filterRow: OptionalFunc,
        paging: OptionalObject,
        sorting: OptionalArray,
        nextPage: OptionalFunc,
        goToPage: OptionalFunc,
        isLoading: OptionalBool,
        action: OptionalNode,
    }

    constructor(props, context) {
        super(props, context);
        const defaultSortingOption = _.find(_.get(props, 'sorting', []), { default: true });
        this.state = {
            sortBy: defaultSortingOption ? defaultSortingOption.value : null,
            sortOrder: defaultSortingOption ? defaultSortingOption.order : null,
        };
    }

    filter() {
        let search = this.props.search || this.state.search || '';
        if (this.state.exact) {
            search = search.replace(/^"+|"+$/g, '');
        }
        const filter = this.props.filter;
        const { items, filterRow } = this.props;
        if (filterRow && (search || filter)) {
            return this.sort(_.filter(items, i => filterRow(i, search.toLowerCase())));
        }
        return this.sort(items);
    }

    sort(items) {
        const { sortBy, sortOrder } = this.state;
        if (sortBy) {
            return _.orderBy(items, [sortBy], [sortOrder]);
        }

        return items;
    }

    onSort(e, sortOption) {
        e.preventDefault();
        const { sortBy, sortOrder } = this.state;
        if (sortOption.value === sortBy) {
            this.setState({ sortOrder: sortOrder === 'asc' ? 'desc' : 'asc' },()=>{
                if (this.props.onSortChange) {
                    this.props.onSortChange({ sortBy: this.state.sortBy, sortOrder: this.state.sortOrder })
                }
            });
        } else {
            this.setState({ sortBy: sortOption.value, sortOrder: sortOption.order }, ()=>{
                if (this.props.onSortChange) {
                    this.props.onSortChange({ sortBy: this.state.sortBy, sortOrder: this.state.sortOrder })
                }
            });
        }
    }

    renderContainer = (children) => {
        const renderRow = ({ index, style }) => (
            <div style={style}>
                {this.props.renderRow(children[index])}
            </div>
        );
        if (children && children.length > 100 && this.props.itemHeight) {
            return (
                <List
                  style={{ overflowX: 'hidden' }}
                  height={this.props.itemHeight * 10}
                  itemCount={children.length}
                  itemSize={this.props.itemHeight}
                  width="100%"
                >
                    {renderRow}
                </List>
            );
        }
        return children.map(this.props.renderRow);
    }

    render() {
        const { sortBy, sortOrder } = this.state;
        const { title, items, renderRow, renderNoResults, paging, prevPage, nextPage, goToPage, isLoading, sorting, action } = this.props;
        const filteredItems = this.filter(items);
        const currentSort = _.find(sorting, { value: sortBy });

        let search = this.props.search || this.state.search || '';
        if (this.state.exact) {
            search = search.replace(/^"+|"+$/g, '');
        }
        return (!search && (!filteredItems || !filteredItems.length)) && !this.props.isLoading && !this.props.renderSearchWithNoResults ? renderNoResults : (
            <Panel
              className={this.props.className}
              title={this.props.title}
              icon={this.props.icon}
              renderFooter={this.props.renderFooter}
              action={this.props.filterRow || this.props.sorting ? (
                  <Row>
                      {!!this.props.sorting && (
                      <Row className="mr-3 relative">
                          <Popover
                            renderTitle={toggle => (
                                <a onClick={toggle}>
                                    <div
                                      className="flex-column ion ion-md-funnel"
                                    />
                                    {currentSort ? currentSort.label : 'Unsorted'}
                                </a>
                            )}
                          >
                              {toggle => (
                                  <div className="popover-inner__content">
                                      {this.props.sorting.map(sortOption => (
                                          <a
                                            className="popover-bt__list-item"
                                            href="#" onClick={(e) => {
                                                this.onSort(e, sortOption);
                                                toggle();
                                            }}
                                          >
                                              <Row space>
                                                  <Row className="flex-1">
                                                      {sortOption.label}
                                                  </Row>
                                                  {currentSort && currentSort.value === sortOption.value && (
                                                  <Row>
                                                      <div
                                                        className={`flex-column ion ${sortOrder === 'asc' ? 'ion-ios-arrow-up' : 'ion-ios-arrow-down'}`}
                                                      />
                                                  </Row>
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
                                  <div className="mr-2" style={{ width: 200 }}>
                                      <Select
                                        className="select-sm"
                                        styles={{
                                            control: base => ({
                                                ...base,
                                                '&:hover': { borderColor: '$bt-brand-secondary' },
                                                border: '1px solid $bt-brand-secondary',
                                                height: 30,
                                            }),
                                        }}
                                        onChange={(v) => {
                                            this.setState({ exact: v.label === 'Exact' });
                                            if (this.props.search) {
                                                this.props.onChange && this.props.onChange(!this.state.exact ? `"${this.props.search}"` : this.props.search.replace(/^"+|"+$/g, ''));
                                            }
                                        }}
                                        value={{ label: this.state.exact ? 'Exact' : this.props.filterLabel || Utils.getIsEdge() ? 'Starts with' : 'Contains' }}
                                        options={[
                                            {
                                                label: Utils.getIsEdge() ? 'Starts with' : 'Contains',
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
                                  <input
                                    ref={c => this.input = c}
                                    onBlur={this.props.onBlur}
                                    onChange={(e) => {
                                        const v = Utils.safeParseEventValue(e);
                                        (this.props.onChange ? this.props.onChange(this.state.exact ? `"${v}"` : v) : this.setState({ search: Utils.safeParseEventValue(e) }));
                                    }}
                                    type="text"
                                    value={search}
                                    className="pl-4"
                                  />
                                  <span style={{ marginLeft: 10, position: 'absolute' }} className="icon ion-ios-search" />
                              </Row>
                          </Row>

                      )}
                  </Row>
              ) : action || null}
            >

                {this.props.searchPanel}
                <div id={this.props.id} className="search-list" style={isLoading ? { opacity: 0.5 } : {}}>
                    {this.props.header}
                    {!!paging && (
                        <Paging
                            paging={paging}
                            isLoading={isLoading}
                            nextPage={nextPage}
                            prevPage={prevPage}
                            goToPage={goToPage}
                        />
                    )}
                    {this.props.isLoading && (!filteredItems||!items) ? <div className="text-center"><Loader/></div> :
                        filteredItems && filteredItems.length
                            ? this.renderContainer(filteredItems) : (renderNoResults && !search) ? renderNoResults : (
                                <Column>
                                    {!isLoading && (
                                        <div className="mx-2 mt-1 mb-2">
                                            {'No results '}
                                            {search && (
                                                <span>
                                                    for
                                                    <strong>
                                                        {` "${search}"`}
                                                    </strong>
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </Column>
                            )
                    }
                </div>
                {!!paging && filteredItems && filteredItems.length > 10 && (
                <Paging
                  paging={paging}
                  isLoading={isLoading}
                  goToPage={goToPage}
                />
                )}
            </Panel>
        );
    }
};

module.exports = PanelSearch;
