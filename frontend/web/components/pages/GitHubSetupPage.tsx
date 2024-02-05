import React, { FC, useState, useEffect } from 'react'
import _data from 'common/data/base/_data'
import OrganisationSelect from 'components/OrganisationSelect'
import ProjectFilter from 'components/ProjectFilter'
import Button from 'components/base/forms/Button'
import { useCreateGithubIntegrationMutation } from 'common/services/useGithubIntegration'
import { useCreateGithubRepositoryMutation } from 'common/services/useGithubRepository'

type GitHubSetupPageType = {}
const GitHubSetupPage: FC<GitHubSetupPageType> = (props) => {
  const reposFaked = {
    'repositories': [
      {
        'description': null,
        'full_name': 'novakzaballa/novak-flagsmith-example',
        'fork': false,
        'id': 727452492,
        'forks_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/forks',
        'name': 'novak-flagsmith-example',
        'collaborators_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/collaborators{/collaborator}',
        'node_id': 'R_kgDOK1wLTA',
        'hooks_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/hooks',
        'owner': {
          'id': 41410593,
          'login': 'novakzaballa',
          'avatar_url': 'https://avatars.githubusercontent.com/u/41410593?v=4',
          'node_id': 'MDQ6VXNlcjQxNDEwNTkz',
          'gravatar_id': '',
          'html_url': 'https://github.com/novakzaballa',
          'url': 'https://api.github.com/users/novakzaballa',
          'followers_url':
            'https://api.github.com/users/novakzaballa/followers',
          'following_url':
            'https://api.github.com/users/novakzaballa/following{/other_user}',
          'gists_url':
            'https://api.github.com/users/novakzaballa/gists{/gist_id}',
          'starred_url':
            'https://api.github.com/users/novakzaballa/starred{/owner}{/repo}',
          'organizations_url': 'https://api.github.com/users/novakzaballa/orgs',
          'subscriptions_url':
            'https://api.github.com/users/novakzaballa/subscriptions',
          'events_url':
            'https://api.github.com/users/novakzaballa/events{/privacy}',
          'repos_url': 'https://api.github.com/users/novakzaballa/repos',
          'received_events_url':
            'https://api.github.com/users/novakzaballa/received_events',
          'site_admin': false,
          'type': 'User',
        },
        'events_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/events',
        'private': false,
        'assignees_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/assignees{/user}',
        'html_url': 'https://github.com/novakzaballa/novak-flagsmith-example',
        'blobs_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/git/blobs{/sha}',
        'branches_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/branches{/branch}',
        'url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example',
        'git_refs_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/git/refs{/sha}',
        'keys_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/keys{/key_id}',
        'git_tags_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/git/tags{/sha}',
        'teams_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/teams',
        'contributors_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/contributors',
        'issue_events_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/issues/events{/number}',
        'commits_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/commits{/sha}',
        'languages_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/languages',
        'comments_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/comments{/number}',
        'tags_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/tags',
        'contents_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/contents/{+path}',
        'statuses_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/statuses/{sha}',
        'compare_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/compare/{base}...{head}',
        'trees_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/git/trees{/sha}',
        'archive_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/{archive_format}{/ref}',
        'stargazers_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/stargazers',
        'downloads_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/downloads',
        'subscribers_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/subscribers',
        'git_commits_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/git/commits{/sha}',
        'subscription_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/subscription',
        'issue_comment_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/issues/comments{/number}',
        'deployments_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/deployments',
        'issues_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/issues{/number}',
        'created_at': '2023-12-04T22:20:48Z',
        'labels_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/labels{/name}',
        'merges_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/merges',
        'milestones_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/milestones{/number}',
        'git_url': 'git://github.com/novakzaballa/novak-flagsmith-example.git',
        'notifications_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/notifications{?since,all,participating}',
        'clone_url':
          'https://github.com/novakzaballa/novak-flagsmith-example.git',
        'pulls_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/pulls{/number}',
        'homepage': null,
        'pushed_at': '2023-12-13T18:18:44Z',
        'releases_url':
          'https://api.github.com/repos/novakzaballa/novak-flagsmith-example/releases{/id}',
        'language': null,
        'size': 5,
        'has_issues': true,
        'updated_at': '2023-12-08T21:39:22Z',
        'has_downloads': true,
        'has_pages': false,
        'ssh_url': 'git@github.com:novakzaballa/novak-flagsmith-example.git',
        'forks_count': 0,
        'svn_url': 'https://github.com/novakzaballa/novak-flagsmith-example',
        'archived': false,
        'stargazers_count': 0,
        'disabled': false,
        'watchers_count': 0,
        'has_discussions': false,
        'allow_forking': true,
        'has_projects': true,
        'has_wiki': true,
        'is_template': false,
        'forks': 0,
        'license': null,
        'mirror_url': null,
        'default_branch': 'master',
        'open_issues': 32,
        'open_issues_count': 32,
        'permissions': {
          'admin': false,
          'maintain': false,
          'pull': false,
          'push': false,
          'triage': false,
        },
        'topics': [],
        'visibility': 'public',
        'watchers': 0,
        'web_commit_signoff_required': false,
      },
    ],
    'repository_selection': 'selected',
    'total_count': 1,
  }
  const installationId =
    new URLSearchParams(props.location.search).get('installation_id') || ''
  const [organisation, setOrganisation] = useState<number>(0)
  const [project, setProject] = useState<number>(0)
  const [repositoryName, setRepositoryName] = useState<string>('')
  const [repositoryOwner, setRepositoryOwner] = useState<string>('')
  const [repositories, setRepositories] = useState<string>('')
  const [
    createGithubIntegration,
    { data, isSuccess: isSuccessCreateGithubIntegration },
  ] = useCreateGithubIntegrationMutation()

  const [createGithubRepository] = useCreateGithubRepositoryMutation()

  const getRepositories = (installationId: string) => {
    // setIsLoading(true)
    console.log('DEBUG: installationId:', installationId)
    _data
      .get(`http://localhost:3000/api/repositories`, {
        'installation_id': installationId,
      })
      .catch((error) => {
        console.log(error)
      })
      .then((res) => {
        // setIsLoading(false)
        setRepositories(reposFaked)
        setRepositoryOwner(reposFaked.repositories[0].owner.login)
        console.log('DEBUG: res:', res)
        // setProjects(res.items)
      })
  }

  useEffect(() => {
    getRepositories(installationId)
  }, [])

  useEffect(() => {
    if (isSuccessCreateGithubIntegration) {
      toast('Saved2')
    }
  }, [isSuccessCreateGithubIntegration])

  useEffect(() => {
    if (data && isSuccessCreateGithubIntegration) {
      createGithubRepository({
        body: {
          project: project,
          repository_name: repositoryName,
          repository_owner: repositoryOwner,
        },
        github_pk: data.id,
        organisation_pk: organisation,
      })
    }
  }, [data, isSuccessCreateGithubIntegration])

  console.log('DEBUG: organisation:', organisation)

  return (
    <div
      id='login-page'
      style={{ flexDirection: 'column' }}
      className='ml-4 bg-light200'
    >
      <h3>Configure your integration with GitHub</h3>
      <InputGroup
        value={installationId}
        data-test='InstallationId'
        inputProps={{
          name: 'InstallationId',
        }}
        disabled
        type='text'
        className={{ width: '500px' }}
        title={'GitHub App Installation Id'}
      />
      <div className='mr-4 mb-4'>
        <p>Select your Organisation</p>
        <OrganisationSelect
          onChange={(organisationId) => {
            setOrganisation(organisationId)
          }}
          showSettings={false}
          firstOrganisation
        />
      </div>
      <Row className='mr-4 mb-4'>
        <div style={{ minWidth: '300px' }}>
          <ProjectFilter
            showAll
            organisationId={organisation}
            onChange={setProject}
            value={project}
          />
        </div>
        <Input
          value={repositoryOwner}
          data-test='repositoryOwner'
          inputProps={{
            name: 'repositoryOwner',
          }}
          onChange={(e) => setRepositoryOwner(Utils.safeParseEventValue(e))}
          disabled
          type='text'
          title={'Repository Owner'}
          inputClassName='input--wide'
          placeholder='repositoryOwner'
        />
        <div style={{ width: '300px' }}>
          <Select
            size='select-md'
            placeholder={'Select your repository'}
            onChange={(v) => setRepositoryName(v.label)}
            options={repositories?.repositories?.map((r) => {
              return { label: r.name, value: r.name }
            })}
          />
        </div>
      </Row>
      <Button
        className='mr-2 text-right'
        theme='primary'
        disabled={!project || !installationId || !repositoryName}
        onClick={() => {
          createGithubIntegration({
            body: {
              installation_id: installationId,
            },
            organisation_pk: organisation,
          })
        }}
      >
        Save
      </Button>
    </div>
  )
}

export default GitHubSetupPage
