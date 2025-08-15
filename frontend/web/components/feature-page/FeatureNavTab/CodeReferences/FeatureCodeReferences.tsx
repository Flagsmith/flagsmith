import { useGetFeatureCodeReferencesQuery } from 'common/services/useCodeReferences'
import moment from 'moment'
import React from 'react'
import CodeReferencesTabHeader from './CodeReferencesTabHeader'
import CodeReferencesByRepoList from './CodeReferencesByRepoList'

export interface CodeReference {
  file_path: string
  line_number: number
  permalink: string
  repository_url: string
  vcs_provider: 'github' | 'gitlab' | 'bitbucket'
}

interface FeatureCodeReferencesProps {
  featureId: number
  projectId: number
}

const FeatureCodeReferences: React.FC<FeatureCodeReferencesProps> = ({
  featureId,
  projectId,
}) => {
  const { data, isLoading } = useGetFeatureCodeReferencesQuery({
    featureId: featureId,
    projectId: projectId,
  })
  const firstScannedAt = data?.first_scanned_at
    ? moment(data.first_scanned_at, 'YYYY-MM-DD')
    : null
  const lastScannedAt = data?.last_scanned_at
    ? moment(data.last_scanned_at, 'YYYY-MM-DD')
    : null

  if (!data || data?.code_references?.length === 0) {
    return (
      <div className='flex flex-col gap-5'>
        <p className='text-sm text-gray-500'>No code references found</p>
      </div>
    )
  }

  const codeReferencesByRepo = data.code_references.reduce((acc, curr) => {
    acc[curr.repository_url] = [...(acc[curr.repository_url] || []), curr]
    return acc
  }, {} as Record<string, CodeReference[]>)

  return (
    <div className='flex flex-col gap-4'>
      {firstScannedAt && lastScannedAt && (
        <CodeReferencesTabHeader
          firstScannedAt={firstScannedAt}
          lastScannedAt={lastScannedAt}
        />
      )}
      <CodeReferencesByRepoList codeReferencesByRepo={codeReferencesByRepo} />
    </div>
  )
}

export default FeatureCodeReferences
