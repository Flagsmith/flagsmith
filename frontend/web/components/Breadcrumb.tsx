import React, { FC } from 'react'
import { Link } from 'react-router-dom'

type BreadcrumbType = {
  items: { title: string; url: string }[]
  currentPage: string
}

const Breadcrumb: FC<BreadcrumbType> = ({ currentPage, items }) => {
  return (
    <nav aria-label='breadcrumb'>
      <ol className='breadcrumb mb-2 py-1"'>
        {items?.map((item) => (
          <li key={item.url} className='breadcrumb-item h6 fs-lg lh-sm'>
            <Link className='text-primary' to={item.url}>
              {item.title}
            </Link>
          </li>
        ))}
        <li
          className='breadcrumb-item active h6 text-muted lh-sm '
          aria-current='page'
          style={{ opacity: 0.6 }}
        >
          {currentPage}
        </li>
      </ol>
    </nav>
  )
}

export default Breadcrumb
