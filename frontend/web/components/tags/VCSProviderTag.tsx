import React from 'react'
import { GithubIcon } from 'components/base/icons/GithubIcon'
import GitlabIcon from 'components/base/icons/GitlabIcon'

interface VCSProviderTagProps {
  count: number
  vcsProvider?: 'github' | 'gitlab' | 'bitbucket'
  isWarning?: boolean
}

const VCSProviderTag: React.FC<VCSProviderTagProps> = ({
  count,
  isWarning = false,
  vcsProvider = 'github',
}) => {
  return (
    <div className='d-flex align-items-center'>
      <span
        className={`chip chip--xs text-white`}
        style={{
          backgroundColor: isWarning ? '#ff9f43' : '#343a40',
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

export default VCSProviderTag
