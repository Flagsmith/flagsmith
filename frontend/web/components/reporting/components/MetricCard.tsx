import React, { FC, ReactNode } from 'react'
import Card from './Card'
import { MetricItem } from '../services'

interface ProgressBarProps {
  width: string
  color: string
  height?: string
}

interface MetricCardProps {
  // For backward compatibility with existing MetricCard usage
  metric?: MetricItem
  className?: string
  
  // New props for direct usage
  title?: string
  value?: string | number
  variant?: 'simple' | 'complex'
  description?: string
  progressBar?: ProgressBarProps
  children?: ReactNode
  
  // Card wrapper props
  showCardWrapper?: boolean
  cardVariant?: 'default' | 'info'
  padding?: 'p-3' | 'p-4'
  textAlign?: 'text-center' | ''
}

const MetricCard: FC<MetricCardProps> = ({ 
  metric, 
  className = '',
  title,
  value,
  variant = 'simple',
  description,
  progressBar,
  children,
  showCardWrapper = false,
  cardVariant = 'default',
  padding = 'p-4',
  textAlign = ''
}) => {
  // For backward compatibility, use metric if provided
  const displayTitle = title || metric?.description || ''
  const displayValue = value !== undefined ? value : metric?.value
  
  const renderSimpleCard = () => (
    <div className='h-100 d-flex flex-column justify-content-center'>
      <p className='mb-2 fw-bold reporting-metric-title reporting-margin-reset'>
        {displayTitle}
      </p>
      <h2 className='mb-0 reporting-metric-value'>
        {typeof displayValue === 'number' ? displayValue.toLocaleString() : displayValue}
      </h2>
    </div>
  )

  const renderComplexCard = () => (
    <div>
      <div className='text-center mb-3'>
        <p className='fw-bold mb-2 reporting-metric-title reporting-margin-reset'>
          {displayTitle}
        </p>
        <h4 className='mb-0 reporting-metric-value'>
          {typeof displayValue === 'number' ? displayValue.toLocaleString() : displayValue}
        </h4>
      </div>
      
      {progressBar && (
        <div className='mb-3'>
          <div className='d-flex justify-content-between align-items-center mb-2'>
            <span className='text-muted reporting-description-small'>{description}</span>
          </div>
          <div className='progress reporting-progress-bg' style={{ height: progressBar.height || '6px' }}>
            <div 
              className='progress-bar' 
              style={{ 
                width: progressBar.width,
                backgroundColor: progressBar.color
              }}
            ></div>
          </div>
        </div>
      )}
      
      {children}
    </div>
  )

  const renderCardContent = () => (
    <div className={`${className}`}>
      {variant === 'complex' ? renderComplexCard() : renderSimpleCard()}
    </div>
  )

  // If no card wrapper needed, return content directly
  if (!showCardWrapper) {
    return renderCardContent()
  }

  // Use the generic Card component
  const getCardVariant = () => {
    switch (cardVariant) {
      case 'info':
        return 'info'
      default:
        return 'default'
    }
  }

  return (
    <Card 
      variant={getCardVariant()}
      textAlign={textAlign as 'text-left' | 'text-center' | 'text-right'}
      fullHeight={true}
      className={className}
    >
      {renderCardContent()}
    </Card>
  )
}

export default MetricCard
export type { ProgressBarProps, MetricCardProps }
