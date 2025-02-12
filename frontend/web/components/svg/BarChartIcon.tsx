import React from 'react'

interface BarChartIconProps {
  className?: string
}

const BarChartIcon: React.FC<BarChartIconProps> = ({ className }) => {
  return (
    <svg
      xmlns='http://www.w3.org/2000/svg'
      width={24}
      height={24}
      viewBox='0 0 24 24'
      fill='none'
      className={className}
    >
      <path
        fill='#1A2634'
        fillRule='evenodd'
        d='M12 4c-.55 0-1 .45-1 1v15c0 .55.45 1 1 1s1-.45 1-1V5c0-.55-.45-1-1-1Zm7 8c-.55 0-1 .45-1 1v7c0 .55.45 1 1 1s1-.45 1-1v-7c0-.55-.45-1-1-1ZM4 9c0-.55.45-1 1-1s1 .45 1 1v11c0 .55-.45 1-1 1s-1-.45-1-1V9Z'
        clipRule='evenodd'
      />
    </svg>
  )
}

export default BarChartIcon
