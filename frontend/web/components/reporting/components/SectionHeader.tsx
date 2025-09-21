import React, { FC } from 'react'

interface SectionHeaderProps {
  title: string
  description: string
  className?: string
}

const SectionHeader: FC<SectionHeaderProps> = ({ 
  title, 
  description, 
  className = '' 
}) => {
  return (
    <div className={`mb-4 ${className}`}>
      <h3 className='mb-1 reporting-section-title'>
        {title}
      </h3>
      <p className='text-muted mb-0 reporting-section-description'>
        {description}
      </p>
    </div>
  )
}

export default SectionHeader
