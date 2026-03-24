import React, { FC, useState } from 'react'
import { ExternalResource, Res } from 'common/types/responses'
import Utils from 'common/utils/utils'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'
import {
  useGetGitlabProjectsQuery,
  useGetGitlabResourcesQuery,
} from 'common/services/useGitlab'
import Constants from 'common/constants'

export type GitLabResourcesSelectType = {
  onChange: (value: string) => void
  linkedExternalResources: ExternalResource[] | undefined
  projectId: string
  resourceType: string
  value: string[] | undefined // an array of resource URLs
  setResourceType: (value: string) => void
}

type GitLabResourcesValueType = {
  value: string
}

const GitLabResourcesSelect: FC<GitLabResourcesSelectType> = ({
  onChange,
  projectId,
  resourceType,
  setResourceType,
  value,
}) => {
  const gitlabTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITLAB',
  )
  const [selectedProject, setSelectedProject] = useState<string>('')
  const gitlabProjectId = selectedProject
    ? parseInt(selectedProject.split('::')[0])
    : undefined
  const projectName = selectedProject
    ? selectedProject.split('::')[1]
    : undefined

  const { data: gitlabProjects } = useGetGitlabProjectsQuery({
    project_id: parseInt(projectId),
  })

  const { data, isFetching, isLoading, searchItems } = useInfiniteScroll<
    Req['getGitlabResources'],
    Res['gitlabResources']
  >(
    useGetGitlabResourcesQuery,
    {
      gitlab_project_id: gitlabProjectId || 0,
      gitlab_resource: resourceType,
      page_size: 100,
      project_id: parseInt(projectId),
      project_name: projectName || '',
    },
    100,
    { skip: !resourceType || !projectId || !gitlabProjectId || !projectName },
  )

  const [searchText, setSearchText] = React.useState('')

  return (
    <>
      <label className='cols-sm-2 control-label'>
        Link new Issue / Merge Request
      </label>
      <div className='d-flex gap-2 mb-2'>
        <div style={{ width: 300 }}>
          <Select
            className='react-select w-100'
            size='select-md'
            placeholder={'Select Your Repository'}
            value={
              gitlabProjects?.results
                ?.map((p) => ({
                  label: p.path_with_namespace,
                  value: `${p.id}::${p.path_with_namespace}`,
                }))
                .find((v) => v.value === selectedProject) || null
            }
            onChange={(v: any) => setSelectedProject(v?.value)}
            options={gitlabProjects?.results?.map((p) => ({
              label: p.path_with_namespace,
              value: `${p.id}::${p.path_with_namespace}`,
            }))}
          />
        </div>
        <div style={{ width: 200 }}>
          <Select
            autoSelect
            className='w-100 react-select'
            size='select-md'
            placeholder={'Select Type'}
            value={gitlabTypes.find((v) => v.resourceType === resourceType)}
            onChange={(v: { resourceType: string }) =>
              setResourceType(v.resourceType)
            }
            options={gitlabTypes.map((e) => {
              return {
                label: e.label,
                resourceType: e.resourceType,
                value: e.id,
              }
            })}
          />
        </div>
      </div>
      {!!gitlabProjectId && !!projectName && (
        <div>
          <Select
            filterOption={(options: any[]) => {
              return options
            }}
            value={null}
            size='select-md'
            placeholder={'Select Your Resource'}
            onChange={(v: GitLabResourcesValueType) => {
              onChange(v?.value)
            }}
            options={data?.results
              .filter((v) => !value?.includes(v.web_url))
              .map((i: Res['GitlabResource']) => {
                return {
                  label: `${i.title} !${i.iid}`,
                  value: i,
                }
              })}
            noOptionsMessage={() =>
              isLoading || isFetching ? (
                <div className='py-2'>
                  <Loader />
                </div>
              ) : (
                'No Results found'
              )
            }
            onInputChange={(e: any) => {
              setSearchText(e)
              searchItems(Utils.safeParseEventValue(e))
            }}
            data={{ searchText }}
          />
        </div>
      )}
    </>
  )
}

export default GitLabResourcesSelect
