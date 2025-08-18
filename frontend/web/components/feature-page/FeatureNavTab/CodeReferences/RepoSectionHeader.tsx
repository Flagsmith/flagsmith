import Icon from 'components/Icon'
import VCSProviderTag from 'components/tags/VCSProviderTag'
import { getDarkMode } from 'project/darkMode'
import React from 'react'

interface RepoSectionHeaderProps {
  repositoryName: string
  provider: 'github' | 'gitlab' | 'bitbucket'
  count: number
  // countByProviders: Record<'gitlab' | 'github' | 'bitbucket', number>
  isOpen: boolean
  collapsible?: boolean
}

const RepoSectionHeader: React.FC<RepoSectionHeaderProps> = ({
  collapsible = false,
  count,
  isOpen,
  provider,
  repositoryName,
}) => {
  const darkMode = getDarkMode()
  // TODO: would be an enum
  // const providers = Object.keys(countByProviders) as (
  //   | 'gitlab'
  //   | 'github'
  //   | 'bitbucket'
  // )[]

  return (
    <>
      <Row className='flex items-center gap-1'>
        {collapsible && (
          <Icon
            name={isOpen ? 'chevron-up' : 'chevron-down'}
            className='w-4 h-4'
            fill={darkMode ? '#fff' : '#000'}
          />
        )}
        <p
          className='text-sm text-gray-500 mb-0 fw-bold'
          style={{ userSelect: 'none' }}
        >
          {repositoryName}
        </p>
        <div className='ml-2'>
          <a
            href={repositoryName}
            target='_blank'
            rel='noreferrer'
            onClick={(e) => e.stopPropagation()}
          >
            <Icon name='open-external-link' width={12} fill='#6837fc' />
          </a>
        </div>
      </Row>
      <VCSProviderTag count={count} vcsProvider={provider} key={provider} />
      {/* <div className='flex flex-row gap-1'>
        {providers.map((provider) => {
          return (
            <>
              {countByProviders[provider] > 0 && (
                <VCSProviderTag
                  count={countByProviders[provider]}
                  vcsProvider={provider}
                  key={provider}
                />
              )}
            </>
          )
        })}
      </div> */}
    </>
  )
}

export default RepoSectionHeader
