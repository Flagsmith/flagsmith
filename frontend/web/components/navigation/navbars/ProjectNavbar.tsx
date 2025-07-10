import React, { FC } from 'react'
import NavSubLink from 'components/navigation/NavSubLink'
import { barChart, gitBranch, gitCompare } from 'ionicons/icons'
import SegmentsIcon from 'components/svg/SegmentsIcon'
import Permission, { useHasPermission } from 'common/providers/Permission'
import AuditLogIcon from 'components/svg/AuditLogIcon'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'
import OverflowNav from 'components/navigation/OverflowNav'
import ProjectChangeRequestsLink from 'components/ProjectChangeRequestsLink'
type ProjectNavType = {
  environmentId?: string
  projectId?: number
}

const ProjectNavbar: FC<ProjectNavType> = ({ environmentId, projectId }) => {
  const integrations = Object.keys(Utils.getIntegrationData())
  const { permission: projectAdmin } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'ADMIN',
  })
  const projectMetricsTooltipEnabled = Utils.getFlagsmithHasFeature(
    'project_metrics_tooltip',
  )
  return (
    <OverflowNav
      gap={3}
      key='project'
      containerClassName='px-2 pb-1 pb-md-0 pb-mb-0 bg-faint'
      className='py-0 d-flex'
    >
      <NavSubLink
        icon={gitBranch}
        id={`features-link`}
        to={`/project/${projectId}/environment/${environmentId}/features`}
      >
        Environments
      </NavSubLink>
      <NavSubLink
        icon={<SegmentsIcon />}
        id={`segments-link`}
        to={`/project/${projectId}/segments`}
      >
        Segments
      </NavSubLink>
      <Permission level='project' permission='VIEW_AUDIT_LOG' id={projectId}>
        {({ permission }) =>
          permission && (
            <NavSubLink
              icon={<AuditLogIcon />}
              id='audit-log-link'
              to={`/project/${projectId}/audit-log`}
              data-test='audit-log-link'
            >
              Audit Log
            </NavSubLink>
          )
        }
      </Permission>
      <ProjectChangeRequestsLink projectId={projectId} />
      {!!integrations.length && (
        <NavSubLink
          icon={<Icon name='layers' />}
          id='integrations-link'
          to={`/project/${projectId}/integrations`}
        >
          Integrations
        </NavSubLink>
      )}
      {projectMetricsTooltipEnabled && (
        <NavSubLink
          icon={barChart}
          to={`/project/${projectId}/reporting`}
          id='reporting-link'
          disabled
          tooltip={
            Utils.getFlagsmithValue('project_metrics_tooltip') ||
            'Coming soon - fallback'
          }
        >
          Reporting
        </NavSubLink>
      )}
      <NavSubLink
        icon={gitCompare}
        id='compare-link'
        to={`/project/${projectId}/compare`}
      >
        Compare
      </NavSubLink>
      {projectAdmin && (
        <>
          {Utils.getFlagsmithHasFeature('release_pipelines') && (
            <NavSubLink
              icon={<Icon name='flash' />}
              id='release-pipelines-link'
              to={`/project/${projectId}/release-pipelines`}
            >
              Release Pipelines
            </NavSubLink>
          )}
          <NavSubLink
            icon={<Icon name='setting' width={24} />}
            id='project-settings-link'
            to={`/project/${projectId}/settings`}
          >
            Project Settings
          </NavSubLink>
        </>
      )}
    </OverflowNav>
  )
}

export default ProjectNavbar
