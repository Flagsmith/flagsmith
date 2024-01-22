import { FC, useEffect, useState } from 'react'
import Project from 'common/project'
// import * as _data from 'common/data/base/_data'
const data = require('common/data/base/_data')

type ProjectUsageType = {
  projectId: string
}

type usageType = {
  max_features_allowed: number
  max_segment_overrides_allowed: number
  max_segments_allowed: number
  total_features: 11
  total_segments: 8
}

const ProjectUsage: FC<ProjectUsageType> = ({ projectId }) => {
  const [usage, setUsage] = useState<usageType | null>(null)

  useEffect(() => {
    data.get(`${Project.api}projects/${projectId}`).then((res: any) => {
      setUsage(res)
    })
  }, [projectId])

  return (
    <div className='mt-4'>
      <Flex>
        <Row className='mb-2'>
          <h5 className='mb-0' onClick={() => console.log(usage)}>
            Project Usage
          </h5>
        </Row>
        <Flex className='gap-2'>
          <p className='m-0 fs-small fw-normal'>
            Segments:{' '}
            <span>
              {usage?.total_features}/{usage?.max_features_allowed}
            </span>
          </p>
          <p className='m-0 fs-small fw-normal'>
            Features:{' '}
            <span>
              {usage?.total_segments}/{usage?.max_segments_allowed}
            </span>
          </p>
          <p className='m-0 fs-small fw-normal'>
            Segment Overrides:{' '}
            <span>?/{usage?.max_segment_overrides_allowed}</span>
          </p>
        </Flex>
      </Flex>
    </div>
  )
}

export default ProjectUsage
