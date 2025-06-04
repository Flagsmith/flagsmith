import React, { FC, useEffect } from 'react'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import loadCrisp from 'common/loadCrisp'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from 'components/Icon'
import { useGetProjectsQuery } from 'common/services/useProject'
import AccountStore from 'common/stores/account-store'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import GettingStartedItem, {
  GettingStartedItemType,
} from 'components/onboarding/GettingStartedItem'
import GettingStartedResource from 'components/onboarding/GettingStartedResource'
import { links, resources } from 'components/onboarding/data/onboarding.data'

const GettingStartedPage: FC = () => {
  useEffect(() => {
    document.body.classList.add('full-screen')
    return () => {
      document.body.classList.remove('full-screen')
    }
  }, [])
  async function onCrispClick() {
    loadCrisp('8857f89e-0eb5-4263-ab49-a293872b6c19')
    Utils.openChat()
  }

  const organisationId = AccountStore.getOrganisation()?.id
  const { data: projects } = useGetProjectsQuery(
    {
      organisationId,
    },
    {
      skip: !organisationId,
    },
  )
  const project = projects?.[0]?.id
  const { data: flags } = useGetProjectFlagsQuery(
    {
      project: `${project}`,
    },
    {
      skip: !project,
    },
  )
  const { data: environments } = useGetEnvironmentsQuery(
    { projectId: `${project}` },
    {
      skip: !project,
    },
  )
  const { data: segments } = useGetSegmentsQuery(
    { projectId: `${project}` },
    { skip: !project },
  )
  const environment = environments?.results?.[0]?.api_key
  const items: GettingStartedItemType[] = [
    {
      complete: !!projects?.length,
      description:
        'Projects let you create and manage a set of features and configure them between multiple app environments',
      duration: 1,
      link: `/organisation/${organisationId}/projects`,
      testId: 'create-project',
      title: 'Create a Project',
    },
    {
      complete: !!flags?.results?.length,
      description:
        'The first step to using feature flags is to create one in the features page',
      disabledMessage: !project
        ? 'You will need to create a project before creating your first feature'
        : null,
      duration: 1,
      link: `/project/${project}/environment/${environment}/features`,
      title: 'Create a Feature',
    },
    {
      complete: !!segments?.results?.length,
      description:
        'Once your features are setup you can target their rollout with segments',
      disabledMessage: !project
        ? 'You will need to create a project before creating your first segment'
        : null,
      duration: 1,
      icon: 'pie-chart',
      link: `/project/${project}/segments`,
      title: 'Create a Segment',
    },
    {
      description: 'Everything you need to get up-and-running with Flagsmith',
      duration: 5,
      link: 'https://docs.flagsmith.com/quickstart/',
      name: 'quickstart',
      title: 'Quick Start Guide',
    },
    {
      description: "Familiarise yourself with Flagsmith's features",
      duration: 1,
      link: 'https://docs.flagsmith.com/basic-features/',
      name: 'basic-features',
      title: 'Feature Overview',
    },
    {
      description:
        'Integrate Flagsmith’s features into your existing tech stack',
      duration: 1,
      icon: 'layers',
      link: 'https://docs.flagsmith.com/integrations/',
      name: 'integrations',
      title: 'Integrations',
    },
    {
      complete: !!segments?.results?.length,
      description:
        "Compare Flagsmith's free open source and commercial features",
      duration: 1,
      link: 'https://docs.flagsmith.com/version-comparison',
      name: 'version-comparison',
      title: 'Version comparison',
    },
  ]

  return (
    <div className='bg-light100 pb-5'>
      <div className='container-fluid mt-4 px-3'>
        <PageTitle title={'Welcome to Flagsmith'}>
          Here's all the useful links to get you started, if you have any
          questions{' '}
          <Button
            theme='text'
            onClick={onCrispClick}
            className='text-primary gap-2'
            href=''
          >
            let us know
          </Button>
          !
        </PageTitle>
        <div className='row row-gap-4'>
          <div className='col-xxl-9 col-xl-8'>
            <div className='card bg-card py-3 shadow rounded'>
              <h5 className='mb-3 px-3'>Getting Started</h5>
              <hr className='mt-0 py-0' />
              <div className='row px-3 row-gap-4'>
                {items.map((v, i) => (
                  <GettingStartedItem key={i} {...v} />
                ))}
              </div>
            </div>
          </div>

          <div className='col-xxl-3 col-xl-4'>
            <div className='card bg-card h-100 py-3 shadow rounded'>
              <h5 className='mb-3 px-3'>Community links</h5>
              <hr className='mt-0 py-0' />
              <div className='d-flex mb-3 flex-column align-items-start gap-2'>
                {links.map((v) => (
                  <Button key={v.href} theme='text' href={v.href}>
                    <Icon name='link' />
                    {v.title}
                  </Button>
                ))}
              </div>
              <hr className='mt-0 py-0' />
              <h5 className='mb-3 px-3'>Resources</h5>
              <hr className='mt-0 py-0' />
              <div className='d-flex flex-column gap-4'>
                {resources.map((v) => (
                  <GettingStartedResource key={v.url} {...v} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfigProvider(GettingStartedPage)
