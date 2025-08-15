import { useGetFeatureCodeReferencesQuery } from 'common/services/useCodeReferences'
import moment from 'moment'
import React from 'react'
import CodeReferencesTabHeader from './CodeReferencesTabHeader'
import CodeReferencesByRepoList from './CodeReferencesByRepoList'

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

  if (!data || Object.keys(data.by_repository).length === 0) {
    return (
      <div className='flex flex-col gap-5'>
        <p className='text-sm text-gray-500'>No code references found</p>
      </div>
    )
  }

  return (
    <div className='flex flex-col gap-4'>
      {firstScannedAt && lastScannedAt && (
        <CodeReferencesTabHeader
          firstScannedAt={firstScannedAt}
          lastScannedAt={lastScannedAt}
        />
      )}
      <CodeReferencesByRepoList codeReferencesByRepo={data.by_repository} />
    </div>
  )
}

export default FeatureCodeReferences
