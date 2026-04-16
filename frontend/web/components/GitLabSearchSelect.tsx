import React, { FC } from 'react'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'
import { Res, type GitLabIssue, type GitLabMergeRequest } from 'common/types/responses'
import {
  useGetGitLabIssuesQuery,
  useGetGitLabMergeRequestsQuery,
} from 'common/services/useGitlab'

type GitLabSearchSelectProps = {
  projectId: number
  gitlabProjectId: number
  linkType: 'issue' | 'merge_request'
  value: GitLabIssue | GitLabMergeRequest | null
  onChange: (selection: GitLabIssue | GitLabMergeRequest) => void
  linkedUrls: string[]
}

const GitLabSearchSelect: FC<GitLabSearchSelectProps> = ({
  gitlabProjectId,
  linkedUrls,
  linkType,
  onChange,
  projectId,
  value,
}) => {
  const useQuery =
    linkType === 'issue'
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

  return (
    <div>
      <Select
        filterOption={(options: any[]) => options}
        value={value ? { label: `${value.title} #${value.iid}`, value } : null}
        size='select-md'
        placeholder={
          linkType === 'issue'
            ? 'Search issues…'
            : 'Search merge requests…'
        }
        onChange={(v: { value: GitLabIssue | GitLabMergeRequest }) => {
          onChange(v.value)
        }}
        options={data?.results
          ?.filter(
            (r: GitLabIssue | GitLabMergeRequest) =>
              !linkedUrls.includes(r.web_url),
          )
          .map((r: GitLabIssue | GitLabMergeRequest) => ({
            label: `${r.title} #${r.iid}`,
            value: r,
          }))}
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
