import React, { useState, FC } from 'react'
import { chevronDown, chevronUp } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'

interface AccordionCardProps {
  children?: React.ReactNode
  title?: string
  className?: string
  defaultOpen?: boolean
  isLoading?: boolean
}

const AccordionCard: FC<AccordionCardProps> = ({
  children,
  defaultOpen = false,
  isLoading = false,
  title = 'Summary',
}) => {
  const [open, setOpen] = useState(defaultOpen)
  const { contentRef, style: collapsibleStyle } = useCollapsibleHeight(open)

  return (
    <div className='d-flex flex-column px-3 py-3 accordion-card m-0'>
      <div
        style={{
          alignItems: 'center',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
        }}
        onClick={isLoading ? undefined : () => setOpen(!open)}
        className='d-flex flex-row justify-content-between font-weight-medium'
      >
        <div className='d-flex flex-row align-items-center gap-1'>
          {title}
          {isLoading && <Loader width='15px' height='15px' />}
        </div>
        {!isLoading && (
          <span className='p-1' aria-label={open ? 'Collapse' : 'Expand'}>
            <IonIcon
              className='fs-small me-2 text-muted'
              icon={open ? chevronUp : chevronDown}
            />
          </span>
        )}
      </div>
      <div ref={contentRef} style={collapsibleStyle}>
        <div className='mt-2 mb-2'>{children}</div>
      </div>
    </div>
  )
}

export default AccordionCard
