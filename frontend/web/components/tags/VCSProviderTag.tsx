import React from 'react'
import { GithubIcon } from 'components/base/icons/GithubIcon'
import GitlabIcon from 'components/base/icons/GitlabIcon'
import { VCSProvider } from 'common/types/responses'

interface VCSProviderTagProps {
  count: number
  vcsProvider?: VCSProvider
  isWarning?: boolean
}

const VCSProviderTag: React.FC<VCSProviderTagProps> = ({
  count,
  isWarning = false,
  vcsProvider = VCSProvider.GITHUB,
}) => {
  let providerIcon = <></>
  switch (vcsProvider) {
    case VCSProvider.GITHUB:
      providerIcon = (
        <GithubIcon
          width={12}
          height={12}
          className='chip-svg-icon'
          fill={'#ffffff'}
        />
      )
      break
    case VCSProvider.GITLAB:
      providerIcon = (
        <GitlabIcon width={12} height={12} className='chip-svg-icon' />
      )
      break
    case VCSProvider.BITBUCKET:
    default:
      providerIcon = (
        <GithubIcon width={12} height={12} className='chip-svg-icon' />
      )
  }

  return (
    <div className='d-flex align-items-center'>
      <span
        className={`chip chip--xs text-white`}
        style={{
          backgroundColor: isWarning ? '#ff9f43' : '#343a40',
          border: 'none',
        }}
      >
        {providerIcon}
        <span>{count}</span>
      </span>
    </div>
  )
}

export default VCSProviderTag
