import React, { Component } from 'react';
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
        const search = this.props.search || this.state.search || "";
        const filter = this.props.filter;
        const { items, filterRow } = this.props;
        if (filterRow && (search||filter)) {
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
            this.setState({ sortOrder: sortOrder === 'asc' ? 'desc' : 'asc' });
        } else {
            this.setState({ sortBy: sortOption.value, sortOrder: sortOption.order });
        }
    }

    render() {
        const { sortBy, sortOrder } = this.state;
        const { title, items, renderRow, renderNoResults, paging, goToPage, isLoading, sorting, action } = this.props;
        const filteredItems = this.filter(items);
        const currentSort = _.find(sorting, { value: sortBy });

        const search = this.props.search || this.state.search;

        return (!search && (!filteredItems || !filteredItems.length)) && !this.props.renderSearchWithNoResults ? renderNoResults : (
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
                    <Row onClick={() => this.input.focus()}>
                        <input
                          ref={c => this.input = c}
                          onBlur={this.props.onBlur}
                          onChange={e => (this.props.onChange ? this.props.onChange(e) : this.setState({ search: Utils.safeParseEventValue(e) }))}
                          type="text"
                          value={this.props.search || search}
                          className="pl-4"
                        />
                        <span style={{ marginLeft: 10, position: 'absolute' }} className="icon ion-ios-search" />
                    </Row>
                  )}
              </Row>
            ) : action || null}
          >
              {!!paging && (
                <Paging
                  paging={paging}
                  isLoading={isLoading}
                  goToPage={goToPage}
                />
              )}
              {this.props.searchPanel}
              <div id={this.props.id} className="search-list" style={isLoading ? { opacity: 0.5 } : {}}>
                  {this.props.header}
                  {filteredItems && filteredItems.length
                    ? filteredItems.map(renderRow) : (renderNoResults && !search) ? renderNoResults : (
                      <Column>
                          <div className="mx-2 mb-2">
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
                      </Column>
                    )}
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
