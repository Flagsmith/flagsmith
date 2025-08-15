import React from 'react'
import { GithubIcon } from 'components/base/icons/GithubIcon'
import { getDarkMode } from 'project/darkMode'
import GitlabIcon from 'components/base/icons/GitlabIcon'

interface GithubReferencesTagProps {
  count: number
  vcsProvider?: 'github' | 'gitlab'
}

const GithubReferencesTag: React.FC<GithubReferencesTagProps> = ({
  count,
  vcsProvider = 'github',
}) => {
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
        {vcsProvider === 'gitlab' ? (
          <GitlabIcon width={12} height={12} className='chip-svg-icon' />
        ) : (
          <GithubIcon
            width={12}
            height={12}
            className='chip-svg-icon'
            fill={'#ffffff'}
          />
        )}
        <span>{count}</span>
      </span>
    </div>
  )
}

export default GithubReferencesTag
