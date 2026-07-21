import { FC } from 'react'
import InfoMessage from 'components/InfoMessage'
import { useGetProjectQuery } from 'common/services/useProject'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import UsageBar from 'components/shared/UsageBar'
import EnvironmentOverrideUsage from './EnvironmentOverrideUsage'

type ProjectUsageTabProps = {
  projectId: string
}

const ProjectUsageTab: FC<ProjectUsageTabProps> = ({ projectId }) => {
  const { data: project } = useGetProjectQuery({ id: projectId })
  const { data: environments } = useGetEnvironmentsQuery({ projectId })

  const maxFeatures = project?.max_features_allowed
  const maxSegments = project?.max_segments_allowed
  const maxSegmentOverrides = project?.max_segment_overrides_allowed

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
        <div className='d-flex flex-column gap-1' style={{ maxWidth: 400 }}>
          {!!maxFeatures && (
            <UsageBar
              label='Features'
              limit={maxFeatures}
              usage={project?.total_features ?? 0}
            />
          )}
          {!!maxSegments && (
            <UsageBar
              label='Segments'
              limit={maxSegments}
              usage={project?.total_segments ?? 0}
            />
          )}
        </div>
        {!!maxSegmentOverrides && (
          <>
            <Row className='mb-2 mt-3'>
              <h6 className='mb-0'>Segment Overrides (per environment)</h6>
            </Row>
            <div className='d-flex flex-column gap-1' style={{ maxWidth: 400 }}>
              {environments?.results.map((env) => (
                <EnvironmentOverrideUsage
                  key={env.api_key}
                  apiKey={env.api_key}
                  name={env.name}
                  limit={maxSegmentOverrides}
                />
              ))}
            </div>
          </>
        )}
      </Flex>
    </div>
  )
}

export default ProjectUsageTab
