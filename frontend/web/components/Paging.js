// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import propTypes from 'prop-types';
import cn from 'classnames';

export default class Paging extends PureComponent {
    static displayName = 'Paging';

    static propTypes = {
        paging: propTypes.object,
        onPreviousClick: propTypes.func,
        onNextClick: propTypes.func,
        goToPage: propTypes.func,
        isLoading: propTypes.bool,
    };

    render() {
        const { props: {
            paging,
            isLoading,
            goToPage,
        } } = this;
        const currentIndex = paging.currentPage - 1;
        const lastPage = Math.ceil(paging.count / paging.pageSize);
        const spaceBetween = 2;
        // const numberOfPages = Math.ceil(paging.count / paging.pageSize);
        const from = Math.max(0, (currentIndex+1) - spaceBetween);
        const to = Math.min(lastPage, (currentIndex? currentIndex: currentIndex+1) + spaceBetween);
        const range = _.range(from, to);
        if (range.length < 2) {
            return <div/>;
        }
        return (
            <Row className="list-item paging" style={isLoading ? { opacity: 0.5 } : {}}>
                <Button
                  disabled={!paging.previous} className="icon btn-paging ion-ios-arrow-back"
                  onClick={() => goToPage(currentIndex)}
                />
                <Row className="list-item">
                    {!range.includes(0) && (
                      <>
                          <div
                            role="button"
                            className={cn({
                                page: true,
                                'active': currentIndex === 1,
                            })}
                            onClick={paging.currentPage === 1 + 1 ? undefined : () => goToPage(1)}
                          >
                              {1}
                          </div>
                          <div
                            className={cn({
                                page: true,
                            })}>
                              ...
                          </div>
                      </>
                    )}
                    {_.map(range, index => (
                        <div
                          key={index} role="button"
                          className={cn({
                              page: true,
                              'active': currentIndex === index,
                          })}
                          onClick={paging.currentPage === index + 1 ? undefined : () => goToPage(index + 1)}
                        >
                            {index + 1}
                        </div>
                    ))}
                    {!range.includes(lastPage-1) && (
                      <>

                          <div
                            className={cn({
                                page: true,
                            })}
                            onClick={paging.currentPage === lastPage + 1 ? undefined : () => goToPage(1)}
                          >
                              ...
                          </div>
                          <div
                            role="button"
                            className={cn({
                                page: true,
                                'active': currentIndex === lastPage,
                            })}
                            onClick={paging.currentPage === lastPage ? undefined : () => goToPage(lastPage)}
                          >
                              {lastPage}
                          </div>
                      </>
                    )}
                </Row>
                <Button
                  className="icon btn-paging ion-ios-arrow-forward" disabled={!paging.next}
                  onClick={() => goToPage(currentIndex + 2)}
                />
            </Row>
        );
    }
}
