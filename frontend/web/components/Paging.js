// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import propTypes from 'prop-types'
import cn from 'classnames'

export default class Paging extends PureComponent {
  static displayName = 'Paging'

  static propTypes = {
    goToPage: propTypes.func,
    isLoading: propTypes.bool,
    onNextClick: propTypes.func,
    onPreviousClick: propTypes.func,
    paging: propTypes.object,
  }

  render() {
    const {
      props: { goToPage, isLoading, nextPage, paging, prevPage },
    } = this
    const currentIndex = paging.currentPage - 1
    const lastPage = Math.ceil(paging.count / paging.pageSize)
    const spaceBetween = 2
    // const numberOfPages = Math.ceil(paging.count / paging.pageSize);
    const from = Math.max(0, currentIndex + 1 - spaceBetween)
    const to = Math.min(
      lastPage,
      (currentIndex || currentIndex + 1) + spaceBetween,
    )
    const range = _.range(from, to)
    const noPages = range.length < 2
    if (noPages && !(paging.next || paging.previous)) {
      return null
    }
    return (
      <Row className=' paging py-0' style={isLoading ? { opacity: 0.5 } : {}}>
        <Button
          disabled={isLoading || !paging.previous}
          className='icon btn-paging ion-ios-arrow-back'
          onClick={() => prevPage()}
        />
        {paging.currentPage ? (
          <Row>
            {!range.includes(0) && !noPages && (
              <>
                <div
                  role='button'
                  className={cn({
                    'active': currentIndex === 1,
                    page: true,
                  })}
                  onClick={
                    paging.currentPage === 1 + 1 ? undefined : () => goToPage(1)
                  }
                >
                  {1}
                </div>
                <div
                  className={cn({
                    page: true,
                  })}
                >
                  ...
                </div>
              </>
            )}
            {!noPages &&
              _.map(range, (index) => (
                <div
                  key={index}
                  role='button'
                  className={cn({
                    'active': currentIndex === index,
                    page: true,
                  })}
                  onClick={
                    paging.currentPage === index + 1
                      ? undefined
                      : () => goToPage(index + 1)
                  }
                >
                  {index + 1}
                </div>
              ))}
            {!noPages && !range.includes(lastPage - 1) && (
              <>
                <div
                  className={cn({
                    page: true,
                  })}
                  onClick={
                    paging.currentPage === lastPage + 1
                      ? undefined
                      : () => goToPage(1)
                  }
                >
                  ...
                </div>
                <div
                  role='button'
                  className={cn({
                    'active': currentIndex === lastPage,
                    page: true,
                  })}
                  onClick={
                    paging.currentPage === lastPage
                      ? undefined
                      : () => goToPage(lastPage)
                  }
                >
                  {lastPage}
                </div>
              </>
            )}
          </Row>
        ) : (
          !!paging.page && (
            <span>
              Page {paging.page}
              {paging.pageSize && paging.count
                ? ` of ${Math.ceil(paging.count / paging.pageSize)}`
                : ''}
            </span>
          )
        )}
        <Button
          className='icon btn-paging ion-ios-arrow-forward'
          disabled={isLoading || !paging.next}
          onClick={() => nextPage()}
        />
      </Row>
    )
  }
}
