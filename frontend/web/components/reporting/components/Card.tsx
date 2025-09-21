import React, { FC, ReactNode } from 'react'

export type CardVariant = 'default' | 'info' | 'primary' | 'secondary'
export type CardTextAlign = 'text-left' | 'text-center' | 'text-right'

export interface CardProps {
  children: ReactNode
  variant?: CardVariant
  textAlign?: CardTextAlign
  className?: string
  fullHeight?: boolean
}

/**
 * Generic Card component that provides consistent styling across the application
 * 
 * Features:
 * - Theme-aware background colors
 * - Consistent padding and spacing
 * - Support for different variants (default, info, primary, secondary)
 * - Optional full height
 * - Responsive text alignment
 */
const Card: FC<CardProps> = ({
  children,
  variant = 'default',
  textAlign = 'text-left',
  className = '',
  fullHeight = false
}) => {
  // Get background color class based on variant
  const getBackgroundClass = () => {
    switch (variant) {
      case 'info':
        return 'reporting-card-bg-info'
      case 'primary':
        return 'reporting-card-bg-primary'
      case 'secondary':
        return 'reporting-card-bg-secondary'
      default:
        return 'reporting-card-bg'
    }
  }

  // Get card classes
  const getCardClasses = () => {
    const baseClasses = 'card border-0'
    const heightClass = fullHeight ? 'h-100' : ''
    return `${baseClasses} ${heightClass} ${getBackgroundClass()} ${className}`.trim()
  }

  // Get card body classes
  const getCardBodyClasses = () => {
    return `card-body p-4 ${textAlign}`.trim()
  }

  return (
    <div className={getCardClasses()}>
      <div className={getCardBodyClasses()}>
        {children}
      </div>
    </div>
  )
}

export default Card
