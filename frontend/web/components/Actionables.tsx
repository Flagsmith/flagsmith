import React, { useState, type FC } from 'react'
import { ellipsisVerticalCircleOutline } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

type ActionablesProps = {
  children: React.ReactNode
  width?: string
}

// Displays an icon that when hovered expands to the right to show a list of actionable children
export const Actionables: FC<ActionablesProps> = ({ children, width }) => {
  const [showList, setShowList] = useState(false)

  // const onMouseLeave = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
  //   e.stopPropagation()
  //   setShowList(false)
  // }

  return (
    <div
      className='actionables'
      style={{ width: width || 20 }}
      onMouseEnter={() => setShowList(true)}
      onTouchStart={() => setShowList(true)}
      onMouseLeave={() => setShowList(false)}
      onTouchEnd={() => setShowList(false)}
      onClick={(e) => e.stopPropagation()}
    >
      <div className='icon--new-tooltip mr-1'>
        <IonIcon icon={ellipsisVerticalCircleOutline} />
      </div>
      <div className={`list ${showList ? 'showActions' : ''}`}>{children}</div>
    </div>
  )
}
