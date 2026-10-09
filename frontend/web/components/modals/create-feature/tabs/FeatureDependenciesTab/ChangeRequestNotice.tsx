import { FC } from 'react'
import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'
import { DependenciesMode } from './dependenciesMode'

type ChangeRequestNoticeProps = {
  mode: DependenciesMode
  canCreate: boolean
  environmentId: string
  environmentName: string
  projectId: number
}

const ChangeRequestNotice: FC<ChangeRequestNoticeProps> = ({
  canCreate,
  environmentId,
  environmentName,
  mode,
  projectId,
}) => {
  if (mode === 'changeRequest' && !canCreate) {
    return (
      <Banner className='mb-3' title={`Read only in ${environmentName}`}>
        {environmentName} requires change requests, and you don't have
        permission to create them.
      </Banner>
    )
  }
  if (mode === 'changeRequest') {
    return (
      <Banner className='mb-3'>
        {environmentName} requires change requests. Dependency changes are
        staged here and go live when the change request is published.
      </Banner>
    )
  }
  if (mode === 'readOnly') {
    return (
      <Banner
        type='warning'
        className='mb-3'
        title={`Read only in ${environmentName}`}
        action={
          <Button
            theme='outline'
            size='small'
            href={`/project/${projectId}/environment/${environmentId}/settings`}
          >
            Enable feature versioning
          </Button>
        }
      >
        Dependency changes need feature versioning to go through a change
        request.
      </Banner>
    )
  }
  return null
}

export default ChangeRequestNotice
