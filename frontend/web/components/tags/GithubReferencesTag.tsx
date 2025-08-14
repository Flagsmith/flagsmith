import React from 'react'
import { GithubIcon } from 'components/base/icons/GithubIcon'
import { getDarkMode } from 'project/darkMode'

interface GithubReferencesTagProps {
  count: number
}

const GithubReferencesTag: React.FC<GithubReferencesTagProps> = ({ count }) => {
  const darkMode = getDarkMode()
  return (
    <div className='d-flex align-items-center'>
      <span
        className={`chip me-2 chip--xs text-white`}
        style={{
          backgroundColor: darkMode ? '#343a40' : '#343a40',
          border: 'none',
        }}
      >
        <GithubIcon
          width={12}
          height={12}
          className='chip-svg-icon'
          fill={'#ffffff'}
        />
        <span>{count}</span>
      </span>
    </div>
  )
}

export default GithubReferencesTag
