import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import Permission from 'common/providers/Permission'
import ChangeRequestStore from 'common/stores/change-requests-store'
import classNames from 'classnames'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import EnvironmentLink from './EnvironmentLink'

type EnvironmentNavType = {
  projectId: number
  environmentId: string
  className: string
  mobile?: boolean
}

const EnvironmentNav: FC<EnvironmentNavType> = ({
  className,
  environmentId,
  mobile,
  projectId,
}) => {
  const { data: environments } = useGetEnvironmentsQuery(
    {
      projectId: `${projectId}`,
    },
    { skip: !projectId },
  )
  const environment = environments?.results?.find(
    (v) => v.api_key === environmentId,
  )
  const changeRequestsEnabled = Utils.changeRequestsEnabled(
    environment?.minimum_change_request_approvals,
  )
  const changeRequest = changeRequestsEnabled
    ? ChangeRequestStore.model[environmentId]
    : null
  const changeRequests = changeRequest?.count || 0
  const scheduled =
    (environment && ChangeRequestStore.scheduled[environmentId]?.count) || 0
  const inner = (
    <div
      className={classNames(
        'd-flex flex-column mx-0 py-1 py-md-0 gap-2',
        className,
      )}
    >
      <Permission
        level='environment'
        permission='ADMIN'
        id={environment?.api_key}
      >
        {({ isLoading, permission: environmentAdmin }) =>
          isLoading || !environment ? (
            <div className='text-center'>
              <Loader />
            </div>
          ) : (
            <>
              <EnvironmentLink
                id={mobile ? undefined : 'features-link'}
                icon='features'
                to={`/project/${projectId}/environment/${environmentId}/features`}
              >
                Features
              </EnvironmentLink>
              <EnvironmentLink
                id='change-requests-link'
                icon='timer'
                to={`/project/${projectId}/environment/${environmentId}/scheduled-changes/`}
              >
                <div>
                  Scheduling
                  {scheduled ? (
                    <span className='ml-1 unread d-inline'>{scheduled}</span>
                  ) : null}
                </div>
              </EnvironmentLink>
              <EnvironmentLink
                id={mobile ? undefined : 'change-requests-link'}
                icon='request'
                to={`/project/${projectId}/environment/${environmentId}/change-requests/`}
              >
                <div>
                  Change Requests{' '}
                  {changeRequests ? (
                    <span className='ms-1 unread d-inline'>
                      {changeRequests}
                    </span>
                  ) : null}
                </div>
              </EnvironmentLink>
              <EnvironmentLink
                id={mobile ? undefined : 'users-link'}
                exact
                icon='people'
                to={`/project/${projectId}/environment/${environmentId}/users`}
              >
                Identities
              </EnvironmentLink>
              <EnvironmentLink
                id={mobile ? undefined : 'sdk-keys-link'}
                icon='code'
                exact
                to={`/project/${projectId}/environment/${environmentId}/sdk-keys`}
              >
                SDK Keys
              </EnvironmentLink>
              {Utils.getFlagsmithHasFeature('split_testing') && (
                <EnvironmentLink
                  id={mobile ? undefined : 'split-tests-link'}
                  exact
                  icon='flask'
                  to={`/project/${projectId}/environment/${environmentId}/split-tests`}
                >
                  Split Tests
                </EnvironmentLink>
              )}
              {environmentAdmin && (
                <EnvironmentLink
                  icon='setting'
                  id={mobile ? undefined : 'env-settings-link'}
                  className='aside__environment-list-item'
                  to={`/project/${projectId}/environment/${environmentId}/settings`}
                >
                  Environment Settings
                </EnvironmentLink>
              )}
            </>
          )
        }
      </Permission>
    </div>
  )
  return inner
}

export default EnvironmentNav
