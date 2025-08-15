import React from 'react'
import { RepositoryCodeReferenceScan } from 'common/types/responses'
import RepoCodeReferencesSection from './RepoCodeReferencesSection'

interface CodeReferencesByRepoListProps {
  codeReferencesByRepo: Record<string, RepositoryCodeReferenceScan>
}

const CodeReferencesByRepoList: React.FC<CodeReferencesByRepoListProps> = ({
  codeReferencesByRepo,
}) => {
  const codeReferencesRepos = Object.keys(codeReferencesByRepo)
  return (
    <div className='flex flex-col gap-3'>
      {codeReferencesRepos.map((repo) => (
        <RepoCodeReferencesSection
          repositoryScan={codeReferencesByRepo[repo]}
          key={repo}
          repositoryName={repo}
        />
      ))}
    </div>
  )
}

export default CodeReferencesByRepoList
