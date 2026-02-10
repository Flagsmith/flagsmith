import React, { FC, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import PageTitle from 'components/PageTitle'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import { useGetProjectQuery } from 'common/services/useProject'
import Panel from 'components/base/grid/Panel'
import Icon from 'components/Icon'
import TagValues from 'components/tags/TagValues'
import Switch from 'components/Switch'
import { Link } from 'react-router-dom'
import Button from 'components/base/forms/Button'

type RouteParams = {
  projectId: string
  flagId: string
}

const FlagEnvironmentsPage: FC = () => {
  const { projectId, flagId } = useParams<RouteParams>()

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

  // Fetch all feature states for this flag across all environments
  const { data: featureStates, isLoading: featureStatesLoading } =
    useGetFeatureStatesQuery(
      {
        feature: Number(flagId),
      },
      { skip: !flagId },
    )

  // Map environments with their feature states
  const environmentStates = useMemo(() => {
    if (!environments?.results) return []

    return environments.results.map((env) => {
      const state = featureStates?.results?.find(
        (fs) => fs.environment === env.id && !fs.live_from,
      )
      return {
        environment: env,
        enabled: state?.enabled ?? flag?.default_enabled ?? false,
        value: state?.feature_state_value,
        featureState: state,
      }
    })
  }, [environments, featureStates, flag])

  // Get scheduled changes
  const scheduledChanges = useMemo(() => {
    if (!featureStates?.results) return []

    const now = new Date()
    return featureStates.results
      .filter((fs) => fs.live_from && new Date(fs.live_from) > now)
      .sort((a, b) =>
        new Date(a.live_from!).getTime() - new Date(b.live_from!).getTime()
      )
  }, [featureStates])

  const isLoading = flagLoading || environmentsLoading || featureStatesLoading

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
          <Link to={`/organisation/${project.organisation}/release-manager`}>
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
              {environmentStates.map(({ environment, enabled, value }) => (
                <tr key={environment.id}>
                  <td>
                    <div className='d-flex align-items-center gap-2'>
                      <Icon name='environment' width={16} fill='#9DA4AE' />
                      <strong>{environment.name}</strong>
                    </div>
                  </td>
                  <td className='text-center'>
                    <Switch checked={enabled} disabled className='switch-sm' />
                  </td>
                  <td className='text-center'>
                    {value !== null && value !== undefined
                      ? typeof value === 'object'
                        ? JSON.stringify(value)
                        : String(value)
                      : flag.initial_value !== null &&
                        flag.initial_value !== undefined
                      ? typeof flag.initial_value === 'object'
                        ? JSON.stringify(flag.initial_value)
                        : String(flag.initial_value)
                      : '-'}
                  </td>
                  <td className='text-center'>
                    {flag.num_segment_overrides && flag.num_segment_overrides > 0
                      ? `${flag.num_segment_overrides} segment${
                          flag.num_segment_overrides > 1 ? 's' : ''
                        }`
                      : '-'}
                  </td>
                  <td className='text-center'>
                    {flag.num_identity_overrides &&
                    flag.num_identity_overrides > 0
                      ? `${flag.num_identity_overrides} ${
                          flag.num_identity_overrides > 1
                            ? 'identities'
                            : 'identity'
                        }`
                      : '-'}
                  </td>
                  <td className='text-center'>
                    <Link
                      to={`/project/${projectId}/environment/${environment.api_key}/features?feature=${flag.id}`}
                      className='btn btn-sm btn-outline-primary'
                    >
                      Manage
                    </Link>
                  </td>
                </tr>
              ))}
              {environmentStates.length === 0 && (
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

      {scheduledChanges.length > 0 && (
        <Panel
          title={
            <div className='d-flex align-items-center gap-2'>
              <Icon name='calendar' width={20} fill='#9DA4AE' />
              <span>Scheduled Changes</span>
              <span className='badge badge-primary'>{scheduledChanges.length}</span>
            </div>
          }
          className='mt-4'
        >
          <div className='table-responsive'>
            <table className='table table-hover mb-0'>
              <thead>
                <tr>
                  <th>Environment</th>
                  <th className='text-center'>Scheduled For</th>
                  <th className='text-center'>New Status</th>
                  <th className='text-center'>New Value</th>
                </tr>
              </thead>
              <tbody>
                {scheduledChanges.map((change) => {
                  const env = environments?.results?.find(
                    (e) => e.id === change.environment,
                  )
                  return (
                    <tr key={change.id}>
                      <td>
                        <div className='d-flex align-items-center gap-2'>
                          <Icon name='environment' width={16} fill='#9DA4AE' />
                          <strong>{env?.name || 'Unknown'}</strong>
                        </div>
                      </td>
                      <td className='text-center'>
                        {change.live_from
                          ? new Date(change.live_from).toLocaleString()
                          : '-'}
                      </td>
                      <td className='text-center'>
                        <Switch
                          checked={change.enabled}
                          disabled
                          className='switch-sm'
                        />
                      </td>
                      <td className='text-center'>
                        {change.feature_state_value !== null &&
                        change.feature_state_value !== undefined
                          ? typeof change.feature_state_value === 'object'
                            ? JSON.stringify(change.feature_state_value)
                            : String(change.feature_state_value)
                          : '-'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  )
}

export default FlagEnvironmentsPage
