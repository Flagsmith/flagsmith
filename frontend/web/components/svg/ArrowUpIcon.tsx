import React from 'react'

interface ArrowUpIconProps {
  className?: string
  height?: string | number
  width?: string | number
}

const ArrowUpIcon: React.FC<ArrowUpIconProps> = ({
  className,
  height,
  width = '100%',
}) => {
  return (
    <svg className={className} width={width} height={height} viewBox='0 0 11 7'>
      <path
        d='M10.888 6.399l-.49.49a.297.297 0 01-.421 0L5.495 2.416 1.012 6.89a.297.297 0 01-.42 0l-.49-.49a.297.297 0 010-.421L5.283.795a.297.297 0 01.42 0l5.184 5.183a.297.297 0 010 .42z'
        fill='#63f'
        fillRule='nonzero'
      />
    </svg>
  )
}

export default ArrowUpIcon
