import React, { FC } from 'react'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'
import {
  Res,
  type GitLabIssue,
  type GitLabMergeRequest,
} from 'common/types/responses'
import {
  useGetGitLabIssuesQuery,
  useGetGitLabMergeRequestsQuery,
} from 'common/services/useGitlab'
import type { GitLabLinkType } from './GitLabLinkSection'

type GitLabSearchSelectProps = {
  projectId: number
  gitlabProjectId: number
  linkType: GitLabLinkType
  value: GitLabIssue | GitLabMergeRequest | null
  onChange: (selection: GitLabIssue | GitLabMergeRequest) => void
  linkedUrls: string[]
}

const GitLabSearchSelect: FC<GitLabSearchSelectProps> = ({
  gitlabProjectId,
  linkType,
  linkedUrls,
  onChange,
  projectId,
  value,
}) => {
  const useQuery =
    linkType === 'GITLAB_ISSUE'
      ? useGetGitLabIssuesQuery
      : (useGetGitLabMergeRequestsQuery as typeof useGetGitLabIssuesQuery)

  const { data, isFetching, isLoading, searchItems } = useInfiniteScroll<
    Req['getGitLabIssues'],
    Res['gitlabIssues']
  >(
    useQuery,
    {
      gitlab_project_id: gitlabProjectId,
      page_size: 100,
      project_id: projectId,
    },
    100,
    { skip: !gitlabProjectId },
  )

  const options = data?.results
    ?.filter((r) => !linkedUrls.includes(r.web_url))
    .map((r) => ({ label: `${r.title} #${r.iid}`, value: r }))

  return (
    <div>
      <Select
        filterOption={(options: any[]) => options}
        value={value ? { label: `${value.title} #${value.iid}`, value } : null}
        size='select-md'
        placeholder={
          linkType === 'GITLAB_ISSUE'
            ? 'Search issues…'
            : 'Search merge requests…'
        }
        onChange={(v: { value: GitLabIssue | GitLabMergeRequest }) => {
          onChange(v.value)
        }}
        options={options}
        noOptionsMessage={() =>
          isLoading || isFetching ? (
            <div className='py-2'>
              <Loader />
            </div>
          ) : (
            'No results found'
          )
        }
        onInputChange={(e: string) => searchItems(e)}
      />
    </div>
  )
}

export default GitLabSearchSelect
