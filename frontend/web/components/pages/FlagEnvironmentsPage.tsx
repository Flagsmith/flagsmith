import React, { FC, useMemo, useState } from 'react'
import { Link, useHistory, useLocation, useParams } from 'react-router-dom'
import PageTitle from 'components/PageTitle'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import { useGetProjectQuery } from 'common/services/useProject'
import Panel from 'components/base/grid/Panel'
import Icon from 'components/Icon'
import TagValues from 'components/tags/TagValues'
import Switch from 'components/Switch'
import Button from 'components/base/forms/Button'
import { Environment, ProjectFlag } from 'common/types/responses'
import Constants from 'common/constants'
import CreateFlagModal from 'components/modals/create-feature'

type RouteParams = {
  projectId: string
  flagId: string
}

type EnvironmentRowProps = {
  environment: Environment
  flag: ProjectFlag
  projectId: string
  onManage: (environmentId: string, tab?: string) => void
}

const EnvironmentRow: FC<EnvironmentRowProps> = ({
  environment,
  flag,
  projectId,
  onManage,
}) => {
  // Fetch feature states for this specific environment to get the current state
  const { data: featureStates, isLoading } = useGetFeatureStatesQuery(
    {
      environment: environment.id,
      feature: flag.id,
    },
    { skip: !environment.id || !flag.id },
  )

  const currentState = useMemo(() => {
    if (!featureStates?.results) return null
    // Find the current state (without live_from or scheduled)
    return featureStates.results.find((fs) => !fs.live_from && !fs.feature_segment && !fs.identity)
  }, [featureStates])

  const enabled = currentState?.enabled ?? flag.default_enabled
  const value = currentState?.feature_state_value ?? flag.initial_value

  // Use project-level counts (not per-environment, but better than nothing)
  const segmentOverridesCount = flag.num_segment_overrides || 0
  const identityOverridesCount = flag.num_identity_overrides || 0

  return (
    <tr>
      <td>
        <div className='d-flex align-items-center gap-2'>
          <Icon name='environment' width={16} fill='#9DA4AE' />
          <strong>{environment.name}</strong>
        </div>
      </td>
      <td className='text-center'>
        {isLoading ? (
          <small className='text-muted'>...</small>
        ) : (
          <Switch checked={enabled} disabled className='switch-sm' />
        )}
      </td>
      <td className='text-center'>
        {value !== null && value !== undefined
          ? typeof value === 'object'
            ? JSON.stringify(value)
            : String(value)
          : flag.initial_value !== null && flag.initial_value !== undefined
          ? typeof flag.initial_value === 'object'
            ? JSON.stringify(flag.initial_value)
            : String(flag.initial_value)
          : '-'}
      </td>
      <td className='text-center'>
        {segmentOverridesCount > 0 ? (
          <button
            onClick={() =>
              onManage(
                environment.api_key,
                Constants.featurePanelTabs.SEGMENT_OVERRIDES,
              )
            }
            className='btn btn-link text-decoration-none p-0'
          >
            {segmentOverridesCount} segment
            {segmentOverridesCount > 1 ? 's' : ''}
          </button>
        ) : (
          '-'
        )}
      </td>
      <td className='text-center'>
        {identityOverridesCount > 0 ? (
          <button
            onClick={() =>
              onManage(
                environment.api_key,
                Constants.featurePanelTabs.IDENTITY_OVERRIDES,
              )
            }
            className='btn btn-link text-decoration-none p-0'
          >
            {identityOverridesCount}{' '}
            {identityOverridesCount > 1 ? 'identities' : 'identity'}
          </button>
        ) : (
          '-'
        )}
      </td>
      <td className='text-center'>
        <Button
          onClick={() => onManage(environment.api_key)}
          size='small'
          theme='outline'
        >
          Manage
        </Button>
      </td>
    </tr>
  )
}

const FlagEnvironmentsPage: FC = () => {
  const { projectId, flagId } = useParams<RouteParams>()
  const location = useLocation<{ searchQuery?: string }>()
  const searchQuery = location.state?.searchQuery
  const history = useHistory()

  // Fetch project to get organisation
  const { data: project } = useGetProjectQuery(
    { id: projectId },
    { skip: !projectId },
  )

  // Fetch flag details
  const { data: flag, isLoading: flagLoading } = useGetProjectFlagQuery(
    {
      id: Number(flagId),
      project: projectId,
    },
    { skip: !projectId || !flagId },
  )

  // Fetch environments for the project
  const { data: environments, isLoading: environmentsLoading } =
    useGetEnvironmentsQuery(
      { projectId: Number(projectId) },
      { skip: !projectId },
    )

  const isLoading = flagLoading || environmentsLoading

  const handleManage = (environmentId: string, tab?: string) => {
    openModal(
      flag?.name || 'Edit Feature',
      <CreateFlagModal
        environmentId={environmentId}
        projectId={projectId}
        projectFlag={flag}
        history={history}
        isEdit
        tab={tab}
      />,
      'side-modal create-feature-modal',
    )
  }

  if (isLoading) {
    return (
      <div className='app-container container'>
        <div className='text-center py-5'>
          <Loader />
        </div>
      </div>
    )
  }

  if (!flag) {
    return (
      <div className='app-container container'>
        <div className='text-center text-muted py-5'>Flag not found</div>
      </div>
    )
  }

  return (
    <div className='app-container container'>
      {project?.organisation && (
        <div className='mb-4'>
          <Link
            to={{
              pathname: `/organisation/${project.organisation}/release-manager`,
              search: searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : '',
            }}
          >
            <Button theme='text' size='small' iconLeft='arrow-left'>
              Back to Release Manager
            </Button>
          </Link>
        </div>
      )}

      <PageTitle title={flag.name}>
        {flag.description && (
          <div className='text-muted mt-2'>{flag.description}</div>
        )}
      </PageTitle>

      <Panel
        title={
          <div className='d-flex align-items-center gap-2'>
            <Icon name='flag' width={20} fill='#9DA4AE' />
            <span>Flag Details</span>
          </div>
        }
        className='mb-4'
      >
        <div className='py-3 px-4'>
          <div className='row mb-3'>
            <div className='col-md-3'>
              <strong>Flag ID:</strong>
            </div>
            <div className='col-md-9'>{flag.id}</div>
          </div>
          <div className='row mb-3'>
            <div className='col-md-3'>
              <strong>Type:</strong>
            </div>
            <div className='col-md-9'>{flag.type}</div>
          </div>
          <div className='row mb-3'>
            <div className='col-md-3'>
              <strong>Default Enabled:</strong>
            </div>
            <div className='col-md-9'>
              {flag.default_enabled ? 'Yes' : 'No'}
            </div>
          </div>
          {flag.initial_value !== null && flag.initial_value !== undefined && (
            <div className='row mb-3'>
              <div className='col-md-3'>
                <strong>Initial Value:</strong>
              </div>
              <div className='col-md-9'>
                {typeof flag.initial_value === 'object'
                  ? JSON.stringify(flag.initial_value)
                  : String(flag.initial_value)}
              </div>
            </div>
          )}
          {flag.tags && flag.tags.length > 0 && (
            <div className='row mb-3'>
              <div className='col-md-3'>
                <strong>Tags:</strong>
              </div>
              <div className='col-md-9'>
                <TagValues projectId={projectId} value={flag.tags} />
              </div>
            </div>
          )}
          <div className='row mb-3'>
            <div className='col-md-3'>
              <strong>Created:</strong>
            </div>
            <div className='col-md-9'>
              {new Date(flag.created_date).toLocaleString()}
            </div>
          </div>
          {flag.owners && flag.owners.length > 0 && (
            <div className='row mb-3'>
              <div className='col-md-3'>
                <strong>Owners:</strong>
              </div>
              <div className='col-md-9'>
                {flag.owners.map((owner, index) => (
                  <span key={owner.id}>
                    {owner.first_name || owner.last_name
                      ? `${owner.first_name} ${owner.last_name}`.trim()
                      : owner.email}
                    {index < flag.owners.length - 1 && ', '}
                  </span>
                ))}
              </div>
            </div>
          )}
          {flag.owner_groups && flag.owner_groups.length > 0 && (
            <div className='row mb-3'>
              <div className='col-md-3'>
                <strong>Owner Groups:</strong>
              </div>
              <div className='col-md-9'>
                {flag.owner_groups.map((group, index) => (
                  <span key={group.id}>
                    {group.name}
                    {index < flag.owner_groups.length - 1 && ', '}
                  </span>
                ))}
              </div>
            </div>
          )}
          {flag.is_archived && (
            <div className='row mb-3'>
              <div className='col-md-3'>
                <strong>Status:</strong>
              </div>
              <div className='col-md-9'>
                <span className='badge badge-warning'>Archived</span>
              </div>
            </div>
          )}
          {flag.is_server_key_only && (
            <div className='row mb-3'>
              <div className='col-md-3'>
                <strong>Visibility:</strong>
              </div>
              <div className='col-md-9'>
                <span className='badge badge-info'>Server-side only</span>
              </div>
            </div>
          )}
        </div>
      </Panel>

      <Panel
        title={
          <div className='d-flex align-items-center gap-2'>
            <Icon name='layers' width={20} fill='#9DA4AE' />
            <span>Environment Status</span>
          </div>
        }
      >
        <div className='table-responsive'>
          <table className='table table-hover mb-0'>
            <thead>
              <tr>
                <th>Environment</th>
                <th className='text-center'>Status</th>
                <th className='text-center'>Value</th>
                <th className='text-center'>Segment Overrides</th>
                <th className='text-center'>Identity Overrides</th>
                <th className='text-center'>Actions</th>
              </tr>
            </thead>
            <tbody>
              {environments?.results?.map((environment) => (
                <EnvironmentRow
                  key={environment.id}
                  environment={environment}
                  flag={flag}
                  projectId={projectId}
                  onManage={handleManage}
                />
              ))}
              {(!environments?.results || environments.results.length === 0) && (
                <tr>
                  <td colSpan={6} className='text-center text-muted py-4'>
                    No environments found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  )
}

export default FlagEnvironmentsPage
