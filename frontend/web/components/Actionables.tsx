import React, { useState, type FC } from 'react'
import { ellipsisVerticalCircleOutline } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

type ActionablesProps = {
  children: React.ReactNode[]
  width?: string
  showActions?: boolean
}

// Displays an icon that when hovered expands to the right to show a list of actionable children
export const Actionables: FC<ActionablesProps> = ({
  children,
  width,
  showActions,
}) => {
  // const onMouseLeave = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
  //   e.stopPropagation()
  //   setShowList(false)
  // }
  console.log(children)
  return (
    <div
      className='actionables'
      style={{
        width: showActions ? 48 * children.length - 20 : 20,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <div
        className={`icon--new-tooltip mr-1 ${showActions ? 'hideIcon' : ''}`}
      >
        <IonIcon icon={ellipsisVerticalCircleOutline} />
      </div>
      <div className={`list ${showActions ? 'showActions' : ''}`}>
        {children}
      </div>
    </div>
  )
}
