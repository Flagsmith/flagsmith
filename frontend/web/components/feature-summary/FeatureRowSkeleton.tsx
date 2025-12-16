import React, { FC } from 'react'
import type { CSSProperties } from 'react'

interface FeatureRowSkeletonProps {
  style?: CSSProperties
}

export const FeatureRowSkeleton: FC<FeatureRowSkeletonProps> = ({ style }) => {
  return (
    <div
      className='d-none d-lg-flex align-items-lg-center flex-lg-row list-item py-0 list-item-xs fs-small clickable skeleton-row'
      style={{
        height: 65,
        ...style,
      }}
    >
      <div className='table-column ps-2 px-0 flex-1'>
        <div className='mx-0 flex-1 flex-column justify-content-center'>
          <div className='d-flex align-items-center gap-2'>
            <div className='skeleton skeleton-text' style={{ width: 180 }} />
            <div
              className='skeleton skeleton-badge'
              style={{ height: 20, width: 80 }}
            />
          </div>
        </div>
        <div className='d-none d-lg-flex align-items-center'>
          <div className='table-column px-1 px-lg-2 flex-1 flex-lg-auto d-flex align-items-center'>
            <div className='skeleton skeleton-text' style={{ width: 100 }} />
          </div>
          <div className='table-column d-flex align-items-center justify-content-center'>
            <div
              className='skeleton skeleton-circle'
              style={{ borderRadius: 12, height: 24, width: 40 }}
            />
          </div>
          <div className='table-column px-1 px-lg-2 d-flex align-items-center justify-content-center'>
            <div
              className='skeleton skeleton-circle'
              style={{ height: 32, width: 32 }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default FeatureRowSkeleton
