import React, { FC, useEffect, useMemo, useState } from 'react'
import PageTitle from 'components/PageTitle'
import InputGroup from 'components/base/forms/InputGroup'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetProjectsQuery } from 'common/services/useProject'
import Icon from 'components/Icon'
import TagValues from 'components/tags/TagValues'
import { Link, useHistory, useLocation } from 'react-router-dom'
import Panel from 'components/base/grid/Panel'
import Button from 'components/base/forms/Button'
import Switch from 'components/Switch'
import { ProjectFlag, ProjectSummary } from 'common/types/responses'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useGetTagsQuery } from 'common/services/useTag'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'

type FlagWithProject = ProjectFlag & {
  projectId: number
  projectName: string
}

const ReleaseManagerPage: FC = () => {
  const { organisationId } = useRouteContext()
  const history = useHistory()
  const location = useLocation()

  // Read initial search query from URL
  const urlParams = new URLSearchParams(location.search)
  const initialQuery = urlParams.get('search') || ''

  const [searchInput, setSearchInput] = useState(initialQuery)
  const [activeSearchQuery, setActiveSearchQuery] = useState(initialQuery)
  const [hasSearched, setHasSearched] = useState(!!initialQuery)

  // Update search state when URL changes (e.g., when navigating back)
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const query = params.get('search') || ''
    setSearchInput(query)
    setActiveSearchQuery(query)
    setHasSearched(!!query)
  }, [location.search])

  const handleSearch = () => {
    const trimmedInput = searchInput.trim()
    if (!trimmedInput) return

    // Update URL with search query
    const params = new URLSearchParams()
    params.set('search', trimmedInput)
    history.push({ search: params.toString() })

    setActiveSearchQuery(trimmedInput)
    setHasSearched(true)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSearch()
    }
  }

  const isSearchDisabled = !searchInput || searchInput.trim().length === 0

  // Fetch all projects in the organisation
  const { data: projects, isLoading: projectsLoading } = useGetProjectsQuery(
    { organisationId: Number(organisationId) },
    { skip: !organisationId },
  )

  return (
    <div className='app-container container'>
      <PageTitle title='Release Manager'>
        Search and manage feature flags across all projects in your
        organisation.
      </PageTitle>

      <div className='mb-4'>
        <InputGroup
          title='Search Flags and Tags'
          component={
            <div className='d-flex gap-2'>
              <input
                className='input full-width'
                name='search'
                onKeyDown={handleKeyDown}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSearchInput(e.target.value)
                }
                placeholder='Search for flags or tags across all projects...'
                value={searchInput}
              />
              <Button onClick={handleSearch} disabled={isSearchDisabled}>
                Search
              </Button>
            </div>
          }
        />
      </div>

      {!hasSearched && (
        <div className='text-center text-muted py-5'>
          Enter a search query and click Search to find flags across all
          projects
        </div>
      )}

      {hasSearched && projectsLoading && (
        <div className='text-center'>
          <Loader />
        </div>
      )}

      {hasSearched && !projectsLoading && projects && (
        <FlagsTable projects={projects} searchQuery={activeSearchQuery} />
      )}
    </div>
  )
}

type FlagsTableProps = {
  projects: ProjectSummary[]
  searchQuery: string
}

const FlagsTable: FC<FlagsTableProps> = ({ projects, searchQuery }) => {
  // Collect all flags from all projects
  const projectsData = projects.map((project) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data: flags, isLoading: flagsLoading } = useGetProjectFlagsQuery(
      { project: String(project.id) },
      { skip: !project.id },
    )

    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data: tags } = useGetTagsQuery(
      { projectId: project.id },
      { skip: !project.id },
    )

    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data: environments } = useGetEnvironmentsQuery(
      { projectId: Number(project.id) },
      { skip: !project.id },
    )

    return {
      environments,
      flags,
      isLoading: flagsLoading,
      project,
      tags,
    }
  })

  // Combine all flags
  const allFlags: FlagWithProject[] = useMemo(() => {
    const flags: FlagWithProject[] = []
    projectsData.forEach(({ flags: projectFlags, project }) => {
      if (projectFlags?.results) {
        projectFlags.results.forEach((flag) => {
          flags.push({
            ...flag,
            projectId: project.id,
            projectName: project.name,
          })
        })
      }
    })
    return flags
  }, [projectsData])

  // Build tags map
  const tagsMap = useMemo(() => {
    const map: Record<number, any[]> = {}
    projectsData.forEach(({ project, tags }) => {
      if (tags) {
        map[project.id] = tags
      }
    })
    return map
  }, [projectsData])

  // Get unique environment names and create a map of environments by project
  const { uniqueEnvNames, environmentsByProject } = useMemo(() => {
    const envsByProject: Record<
      number,
      Array<{ id: number; name: string }>
    > = {}
    const envNames = new Set<string>()

    projectsData.forEach(({ environments, project }) => {
      if (environments?.results) {
        envsByProject[project.id] = environments.results.map((env) => ({
          id: env.id,
          name: env.name,
        }))
        environments.results.forEach((env) => {
          envNames.add(env.name)
        })
      }
    })

    return {
      environmentsByProject: envsByProject,
      uniqueEnvNames: Array.from(envNames).sort(),
    }
  }, [projectsData])

  // Filter flags based on search query
  const filteredFlags = useMemo(() => {
    if (!searchQuery) return []

    const query = searchQuery.toLowerCase()
    return allFlags.filter((flag) => {
      const matchesName = flag.name.toLowerCase().includes(query)
      const matchesDescription = flag.description?.toLowerCase().includes(query)

      // Match tags
      const projectTags = tagsMap[flag.projectId] || []
      const flagTags = projectTags.filter((t) => flag.tags?.includes(t.id))
      const matchesTags = flagTags.some((t) =>
        t.label.toLowerCase().includes(query),
      )

      return matchesName || matchesDescription || matchesTags
    })
  }, [allFlags, searchQuery, tagsMap])

  const isLoading = projectsData.some((p) => p.isLoading)

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  return (
    <Panel
      title={
        <div className='d-flex align-items-center gap-2'>
          <Icon name='features' width={20} fill='#9DA4AE' />
          <span>
            Search Results ({filteredFlags.length} flag
            {filteredFlags.length !== 1 ? 's' : ''})
          </span>
        </div>
      }
    >
      {filteredFlags.length === 0 ? (
        <div className='text-center text-muted py-4'>
          No flags found matching "{searchQuery}"
        </div>
      ) : (
        <div className='table-responsive'>
          <table
            className='table table-hover mb-0'
            style={{ fontSize: '0.875rem' }}
          >
            <thead>
              <tr>
                <th style={{ minWidth: '200px' }}>Flag Name</th>
                <th style={{ minWidth: '120px' }}>Project</th>
                <th style={{ minWidth: '150px' }}>Tags</th>
                {uniqueEnvNames.map((envName) => (
                  <th
                    key={envName}
                    className='text-center'
                    style={{ minWidth: '80px' }}
                  >
                    <small className='text-muted'>{envName}</small>
                  </th>
                ))}
                <th className='text-center' style={{ minWidth: '100px' }}>
                  Created
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredFlags.map((flag) => (
                <FlagRow
                  key={`${flag.projectId}-${flag.id}`}
                  flag={flag}
                  uniqueEnvNames={uniqueEnvNames}
                  environmentsByProject={environmentsByProject}
                  searchQuery={searchQuery}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  )
}

type EnvironmentCellProps = {
  flagId: number
  environmentId: number
  defaultEnabled: boolean
}

const EnvironmentCell: FC<EnvironmentCellProps> = ({
  defaultEnabled,
  environmentId,
  flagId,
}) => {
  const { data: featureStates, isLoading } = useGetFeatureStatesQuery(
    {
      environment: environmentId,
      feature: flagId,
    },
    { skip: !flagId || !environmentId },
  )

  const enabled = useMemo(() => {
    if (featureStates?.results && featureStates.results.length > 0) {
      const state = featureStates.results.find((s) => !s.live_from)
      if (state) {
        return state.enabled
      }
    }
    return defaultEnabled
  }, [featureStates, defaultEnabled])

  return (
    <td className='text-center'>
      {isLoading ? (
        <small className='text-muted'>...</small>
      ) : (
        <Switch checked={enabled} disabled className='switch-sm' />
      )}
    </td>
  )
}

type FlagRowProps = {
  flag: FlagWithProject
  uniqueEnvNames: string[]
  environmentsByProject: Record<number, Array<{ id: number; name: string }>>
  searchQuery: string
}

const FlagRow: FC<FlagRowProps> = ({
  environmentsByProject,
  flag,
  searchQuery,
  uniqueEnvNames,
}) => {
  const projectEnvs = useMemo(
    () => environmentsByProject[flag.projectId] || [],
    [environmentsByProject, flag.projectId],
  )

  return (
    <tr>
      <td>
        <Link
          to={`/project/${flag.projectId}/flag/${flag.id}/environments`}
          className='text-decoration-none'
        >
          <div className='d-flex align-items-center gap-2'>
            <Icon name='features' width={14} fill='#9DA4AE' />
            <strong>{flag.name}</strong>
          </div>
          {flag.description && (
            <small className='text-muted d-block mt-1'>
              {flag.description}
            </small>
          )}
        </Link>
      </td>
      <td>
        <small className='text-muted'>{flag.projectName}</small>
      </td>
      <td>
        {flag.tags && flag.tags.length > 0 ? (
          <TagValues projectId={String(flag.projectId)} value={flag.tags} />
        ) : (
          <span className='text-muted'>-</span>
        )}
      </td>
      {uniqueEnvNames.map((envName) => {
        // Find the environment in this flag's project that matches this name
        const projectEnv = projectEnvs.find((e) => e.name === envName)

        if (!projectEnv) {
          // This environment doesn't exist in this flag's project
          return (
            <td key={envName} className='text-center'>
              <span className='text-muted'>-</span>
            </td>
          )
        }

        return (
          <EnvironmentCell
            key={envName}
            flagId={flag.id}
            environmentId={projectEnv.id}
            defaultEnabled={flag.default_enabled}
          />
        )
      })}
      <td className='text-center'>
        <small className='text-muted'>
          {new Date(flag.created_date).toLocaleDateString('en-GB')}
        </small>
      </td>
    </tr>
  )
}

export default ReleaseManagerPage
