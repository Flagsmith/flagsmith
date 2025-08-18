import React from 'react'
import { CodeReference, FeatureCodeReferences } from 'common/types/responses'
import RepoCodeReferencesSection from './RepoCodeReferencesSection'

export type CodeReferencesByRepo = Record<string, FeatureCodeReferences>
// {
//   code_references: CodeReference[]
//   repository_url: string
//   last_successful_repository_scanned_at: string
//   last_feature_found_at: string
//   vcs_provider: string
// }

interface CodeReferencesByRepoListProps {
  codeReferencesByRepo: Record<string, FeatureCodeReferences>
}

const CodeReferencesByRepoList: React.FC<CodeReferencesByRepoListProps> = ({
  codeReferencesByRepo,
}) => {
  const codeReferencesRepos = Object.keys(codeReferencesByRepo)
  return (
    <div className='flex flex-col gap-3'>
      {codeReferencesRepos.map((repo) => (
        <RepoCodeReferencesSection
          key={codeReferencesByRepo[repo].repository_url}
          repositoryName={codeReferencesByRepo[repo].repository_url}
          repositoryScan={codeReferencesByRepo[repo]}
        />
      ))}
    </div>
  )
}

export default CodeReferencesByRepoList
