import React, { FC } from 'react'
import type { CSSProperties } from 'react'

interface FeatureRowSkeletonProps {
  style?: CSSProperties
}

export const FeatureRowSkeleton: FC<FeatureRowSkeletonProps> = ({ style }) => {
  return (
    <div
      className='list-item list-item-sm clickable skeleton-row'
      style={{
        height: 65,
        ...style,
      }}
    >
      <div className='flex-row flex-1 align-items-center gap-3'>
        <div className='skeleton skeleton-text' style={{ width: 180 }} />

        <div className='flex gap-2'>
          <div
            className='skeleton skeleton-badge'
            style={{ height: 20, width: 80 }}
          />
        </div>

        <div className='flex-1' />

        <div className='skeleton skeleton-text' style={{ width: 100 }} />

        <div
          className='skeleton skeleton-circle'
          style={{ borderRadius: 12, height: 24, width: 40 }}
        />

        <div
          className='skeleton skeleton-circle'
          style={{ height: 32, width: 32 }}
        />
      </div>
    </div>
  )
}

export default FeatureRowSkeleton
