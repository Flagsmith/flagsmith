import React from 'react'

type DocPageProps = {
  children: React.ReactNode
  description: React.ReactNode
  title: string
}

const DocPage: React.FC<DocPageProps> = ({ children, description, title }) => (
  <div className='docs-page'>
    <h2 className='docs-page__title'>{title}</h2>
    <p className='docs-page__description'>{description}</p>
    {children}
  </div>
)

export default DocPage
