import React, { FC } from 'react'
import { Link } from 'react-router-dom'

type BreadcrumbType = {
  items: { title: string; url: string }[]
  currentPage: string
}

const Breadcrumb: FC<BreadcrumbType> = ({ currentPage, items }) => {
  return (
    <div className='d-flex align-items-center my-2 py-1'>
      {items?.map((item) => (
        <>
          <Link className='text-primary h6 mb-0' to={item.url}>
            {item.title}
          </Link>
          <div className='text-muted mx-2 h6 mb-0'>/</div>
        </>
      ))}
      {typeof currentPage === 'string' ? (
        <div
          className='active h6 text-muted lh-sm '
          aria-current='page'
          style={{ opacity: 0.6 }}
        >
          {currentPage}
        </div>
      ) : (
        currentPage
      )}
    </div>
  )
}

export default Breadcrumb
