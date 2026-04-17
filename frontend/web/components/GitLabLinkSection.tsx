import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import GitLabProjectSelect from './GitLabProjectSelect'
import GitLabSearchSelect from './GitLabSearchSelect'
import type {
  GitLabIssue,
  GitLabLinkType,
  GitLabMergeRequest,
} from 'common/types/responses'

type GitLabLinkSectionProps = {
  projectId: number
  linkedUrls: string[]
}

const GitLabLinkSection: FC<GitLabLinkSectionProps> = ({
  linkedUrls,
  projectId,
}) => {
  const gitlabTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITLAB',
  )

  const [gitlabProjectId, setGitlabProjectId] = useState<number | null>(null)
  const [linkType, setLinkType] = useState<GitLabLinkType>('issue')
  const [selectedItem, setSelectedItem] = useState<
    GitLabIssue | GitLabMergeRequest | null
  >(null)

  return (
    <div>
      <label className='cols-sm-2 control-label'>
        Link GitLab issue or merge request
      </label>
      <div className='d-flex gap-2 mb-2'>
        <GitLabProjectSelect
          projectId={projectId}
          value={gitlabProjectId}
          onChange={setGitlabProjectId}
        />
        <div style={{ width: 200 }}>
          <Select
            autoSelect
            className='w-100 react-select'
            size='select-md'
            placeholder='Select type'
            value={gitlabTypes.find((v) => v.resourceType === linkType)}
            onChange={(v: { resourceType: GitLabLinkType }) => {
              setLinkType(v.resourceType)
              setSelectedItem(null)
            }}
            options={gitlabTypes.map((e) => ({
              label: e.label,
              resourceType: e.resourceType,
              value: e.id,
            }))}
          />
        </div>
      </div>
      {gitlabProjectId != null && (
        <>
          <GitLabSearchSelect
            projectId={projectId}
            gitlabProjectId={gitlabProjectId}
            linkType={linkType}
            value={selectedItem}
            onChange={(item) => setSelectedItem(item)}
            linkedUrls={linkedUrls}
          />
          <div className='text-right mt-2'>
            <Button disabled theme='primary'>
              Link
            </Button>
          </div>
        </>
      )}
    </div>
  )
}

export default GitLabLinkSection
