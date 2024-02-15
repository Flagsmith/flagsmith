import { FC, useEffect, useState } from 'react'
import Project from 'common/project'
import InfoMessage from './InfoMessage'
import { useGetProjectQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import { Environment } from 'common/types/responses'
const _data = require('common/data/base/_data')

type ProjectUsageType = {
  projectId: string
}

const ProjectUsage: FC<ProjectUsageType> = ({ projectId }) => {
  const { data: project } = useGetProjectQuery({ id: projectId })
  const { data: environments } = useGetEnvironmentsQuery({ projectId })

  const [segmentOverridesUsage, setSegmentOverridesUsage] = useState<number>(0)

  const getSegmentOverridesUsage = (apiKeys: string[]) => {
    apiKeys.forEach((apiKey) => {
      _data
        .get(`${Project.api}environments/${apiKey}`)
        .then((res: Environment) => {
          setSegmentOverridesUsage(
            (prev) => prev + (res.total_segment_overrides || 0),
          )
        })
    })
  }

  useEffect(() => {
    if (environments) {
      const apiKeys = environments.results.map((env) => env.api_key)
      getSegmentOverridesUsage(apiKeys)
    }
  }, [environments])

  return (
    <div className='mt-4'>
      <Flex>
        <Row>
          <InfoMessage>
            In order to ensure consistent performance, Flagsmith has the
            following usage limits.{' '}
            <a
              target='_blank'
              href='https://docs.flagsmith.com/system-administration/system-limits'
              rel='noreferrer'
            >
              <strong>Check the Docs for more details.</strong>
            </a>
          </InfoMessage>
        </Row>
        <Row className='mb-2'>
          <h5 className='mb-0'>Project Usage</h5>
        </Row>
        <Flex className='gap-2'>
          <p className='m-0 fs-small fw-normal'>
            Features:{' '}
            <span className='fw-bold'>
              {project?.total_features}/{project?.max_features_allowed}
            </span>
          </p>
          <p className='m-0 fs-small fw-normal'>
            Segments:{' '}
            <span className='fw-bold'>
              {project?.total_segments}/{project?.max_segments_allowed}
            </span>
          </p>
          <p className='m-0 fs-small fw-normal'>
            Segment Overrides:{' '}
            <span className='fw-bold'>
              {segmentOverridesUsage}/{project?.max_segment_overrides_allowed}
            </span>
          </p>
        </Flex>
      </Flex>
    </div>
  )
}

export default ProjectUsage
