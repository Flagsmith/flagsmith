import { FC, useEffect, useState } from 'react'
import Project from 'common/project'
import InfoMessage from './InfoMessage'
// import * as _data from 'common/data/base/_data'
const _data = require('common/data/base/_data')

type ProjectUsageType = {
  projectId: string
}

type getProjectResponseType = {
  max_features_allowed: number
  max_segment_overrides_allowed: number
  max_segments_allowed: number
  total_features: 11
  total_segments: 8
  [key: string]: any
}

type usageType = {
  max_features_allowed: number
  max_segment_overrides_allowed: number
  max_segments_allowed: number
  total_features: number
  total_segments: number
  total_segment_overrides: {
    [key: string]: number
  }
}

type getEnvironmentsResType = {
  results: {
    api_key: string
    [key: string]: any
  }[]
}

type getEnvironmentResType = {
  [key: string]: any
  total_segment_overrides: number
  id: number
}

const ProjectUsage: FC<ProjectUsageType> = ({ projectId }) => {
  const [usage, setUsage] = useState<Partial<usageType>>({})

  const getSegmentOverridesUsage = (apiKeys: string[]) => {
    apiKeys.forEach((apiKey) => {
      _data
        .get(`${Project.api}environments/${apiKey}`)
        .then((res: getEnvironmentResType) => {
          setUsage((prev) => {
            return {
              ...prev,
              total_segment_overrides: {
                ...prev?.total_segment_overrides,
                [apiKey]: res.total_segment_overrides,
              },
            }
          })
        })
    })
  }

  const reduceTotalSegmentOverrides = () => {
    if (!usage.total_segment_overrides) return 0
    const total = Object.values(usage.total_segment_overrides).reduce(
      (acc, curr) => acc + curr,
      0,
    )
    return total
  }

  useEffect(() => {
    _data
      .get(`${Project.api}projects/${projectId}`)
      .then((res: getProjectResponseType) => {
        console.log(res)
        setUsage({
          max_features_allowed: res.max_features_allowed,
          max_segment_overrides_allowed: res.max_segment_overrides_allowed,
          max_segments_allowed: res.max_segments_allowed,
          total_features: res.total_features,
          total_segment_overrides: {},
          total_segments: res.total_segments,
        })
      })
    _data
      .get(`${Project.api}environments/?project=${projectId}`)
      .then((res: getEnvironmentsResType) => {
        const apiKeys = res.results.map((item) => item.api_key)
        getSegmentOverridesUsage(apiKeys)
      })
  }, [projectId])

  return (
    <div className='mt-4'>
      <Flex>
        <Row>
          <InfoMessage>
            In order to ensure consistent performance, Flagsmith has some{' '}
            <a
              target='_blank'
              href='https://docs.flagsmith.com/system-administration/system-limits'
              rel='noreferrer'
            >
              <strong>System Limits</strong>
            </a>
          </InfoMessage>
        </Row>
        <Row className='mb-2'>
          <h5 className='mb-0' onClick={() => console.log(usage)}>
            Project Usage
          </h5>
        </Row>
        <Flex className='gap-2'>
          <p className='m-0 fs-small fw-normal'>
            Segments:{' '}
            <span className='fw-bold'>
              {usage?.total_features}/{usage?.max_features_allowed}
            </span>
          </p>
          <p className='m-0 fs-small fw-normal'>
            Features:{' '}
            <span className='fw-bold'>
              {usage?.total_segments}/{usage?.max_segments_allowed}
            </span>
          </p>
          <p className='m-0 fs-small fw-normal'>
            Segment Overrides:{' '}
            <span className='fw-bold'>
              {reduceTotalSegmentOverrides()}/
              {usage?.max_segment_overrides_allowed}
            </span>
          </p>
        </Flex>
      </Flex>
    </div>
  )
}

export default ProjectUsage
