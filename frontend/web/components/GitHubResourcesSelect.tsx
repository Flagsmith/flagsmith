import React, { FC, useEffect, useMemo, useState } from 'react'
import { ExternalResource, GithubResource, Res } from 'common/types/responses'
import Utils from 'common/utils/utils'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'
import { useGetGithubResourcesQuery } from 'common/services/useGithub'
import Constants from 'common/constants'
import MyRepositoriesSelect from './MyRepositoriesSelect'

export type GitHubResourcesSelectType = {
  onChange: (value: string) => void
  lastSavedResource: string | undefined
  linkedExternalResources: ExternalResource[] | undefined
  orgId: string
  githubId: string
  resourceType: string
  setResourceType: (value: string) => void
}

type GitHubResourcesValueType = {
  value: string
}
const GitHubResourcesSelect: FC<GitHubResourcesSelectType> = ({
  githubId,
  lastSavedResource,
  onChange,
  orgId,
  resourceType,
  setResourceType,
}) => {
  const githubTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITHUB',
  )
  const [repo, setRepo] = useState('')
  const { repoName, repoOwner } = useMemo(() => {
    if (!repo) {
      return {}
    }
    const [repoOwner, repoName] = repo.split('/')
    return { repoName, repoOwner }
  }, [repo])

  const { data, isFetching, isLoading, searchItems } = useInfiniteScroll<
    Req['getGithubResources'],
    Res['githubResources']
  >(
    useGetGithubResourcesQuery,
    {
      github_resource: resourceType,
      organisation_id: orgId,
      page_size: 100,
      repo_name: `${repoName}`,
      repo_owner: `${repoOwner}`,
    },
    100,
    { skip: !resourceType || !orgId || !repoName || !repoOwner },
  )

  const [selectedOption, setSelectedOption] =
    useState<GitHubResourcesValueType | null>(null)
  const [searchText, setSearchText] = React.useState('')

  useEffect(() => {
    if (selectedOption && selectedOption.value === lastSavedResource) {
      setSelectedOption(null)
    }
  }, [lastSavedResource, selectedOption])

  return (
    <>
      <div className='d-flex gap-2 mb-2'>
        <MyRepositoriesSelect
          githubId={githubId}
          orgId={orgId}
          value={repo}
          onChange={setRepo}
        />
        <div style={{ width: 200 }}>
          <Select
            autoSelect
            className='w-100'
            size='select-md'
            placeholder={'Select Type'}
            value={githubTypes.find((v) => v.resourceType === resourceType)}
            onChange={(v: { resourceType: string }) =>
              setResourceType(v.resourceType)
            }
            options={githubTypes.map((e) => {
              return {
                label: e.label,
                resourceType: e.resourceType,
                value: e.id,
              }
            })}
          />
        </div>
      </div>
      {!!repoName && !!repoOwner && (
        <div>
          <label className='cols-sm-2 control-label'>
            Link new Issue / Pull Request
          </label>
          <Select
            filterOption={(options: any[]) => {
              return options
            }}
            value={selectedOption}
            size='select-md'
            placeholder={'Select Your Resource'}
            onChange={(v: GitHubResourcesValueType) => {
              setSelectedOption(v)
              onChange(v?.value)
            }}
            options={data?.results.map((i: GithubResource) => {
              return {
                label: `${i.title} #${i.number}`,
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

export default GitHubResourcesSelect
