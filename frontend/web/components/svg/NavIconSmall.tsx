import React, { FC } from 'react'

interface NavIconSmallProps {
  className?: string
}

const NavIconSmall: FC<NavIconSmallProps> = ({ className }) => {
  return (
    <svg className={className} viewBox='0 0 320 320'>
      <g>
        <rect
          fill='none'
          id='canvas_background'
          height='322'
          width='322'
          y='-1'
          x='-1'
        />
      </g>
      <g>
        <path
          id='svg_1'
          fill='#fff'
          d='m5.81051,129.451c-15.62702,-52.1207 -7.82114,-101.9751 58.54009,-120.8421c16.8292,-4.7851 42.4824,-8.2425 59.8964,-8.5129c63.566,-0.9882 195.198,-0.2072 198.206,0.0301c1.653,0.1321 -4.709,25.16 -15.856,41.7111c-18.233,27.0704 -44.207,39.7738 -77.023,41.4258c-40.408,2.036 -80.93,2.415 -121.403,2.433c-40.0708,0.021 -74.4522,12 -100.86364,43.243c-0.29116,0.347 -0.98616,0.355 -1.49685,0.512z'
        />
        <path
          id='svg_2'
          fill='#fff'
          d='m205.696,117.206l-107.196,-0.195c-55.5867,0.484 -100.5,45.66 -100.5,101.331c0,55.67 44.9133,100.848 100.5,101.331l0,-130.759l107.196,0l0,-71.708z'
        />
      </g>
    </svg>
  )
}

export default NavIconSmall
