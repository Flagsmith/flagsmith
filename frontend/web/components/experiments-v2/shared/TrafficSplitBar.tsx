import React, { FC } from 'react'
import './TrafficSplitBar.scss'

type Split = {
  name: string
  percentage: number
  colour: string
}

type TrafficSplitBarProps = {
  splits: Split[]
}

const TrafficSplitBar: FC<TrafficSplitBarProps> = ({ splits }) => {
  return (
    <div className='traffic-split-bar'>
      <div className='traffic-split-bar__bar'>
        {splits.map((split, index) => (
          <div
            key={index}
            className='traffic-split-bar__segment'
            style={{
              background: split.colour,
              width: `${split.percentage}%`,
            }}
          />
        ))}
      </div>
      <div className='traffic-split-bar__labels'>
        {splits.map((split, index) => (
          <div key={index} className='traffic-split-bar__label'>
            <span
              className='traffic-split-bar__label-dot'
              style={{ background: split.colour }}
            />
            <span className='traffic-split-bar__label-text'>
              {split.name}: {split.percentage}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

TrafficSplitBar.displayName = 'TrafficSplitBar'
export default TrafficSplitBar
