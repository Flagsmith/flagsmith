import React, { FC } from 'react'
import NavSubLink from 'components/navigation/NavSubLink'
import Permission, { useHasPermission } from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import OverflowNav from 'components/navigation/OverflowNav'
import ProjectChangeRequestsLink from 'components/ProjectChangeRequestsLink'
import { ProjectPermission } from 'common/types/permissions.types'
import {
  BarChartIcon,
  CompareIcon,
  FlashIcon,
  GitBranchIcon,
  LayersIcon,
  ListIcon,
  PieChartIcon,
  RefreshIcon,
  SettingsIcon,
} from 'components/icons'

type ProjectNavType = {
  environmentId?: string
  projectId?: number
}

const ProjectNavbar: FC<ProjectNavType> = ({ environmentId, projectId }) => {
  const integrations = Object.keys(Utils.getIntegrationData())
  const { permission: projectAdmin } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.ADMIN,
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
        icon={<GitBranchIcon />}
        id={`features-link`}
        isActive={(_, location) =>
          location.pathname.startsWith(
            `/project/${projectId}/environment/${environmentId}`,
          )
        }
        to={`/project/${projectId}/environment/${environmentId}/features`}
      >
        Environments
      </NavSubLink>
      <NavSubLink
        icon={<PieChartIcon />}
        id={`segments-link`}
        to={`/project/${projectId}/segments`}
      >
        Segments
      </NavSubLink>
      <NavSubLink
        icon={<RefreshIcon />}
        id='lifecycle-link'
        to={`/project/${projectId}/lifecycle`}
        isActive={(_, location) =>
          location.pathname.startsWith(`/project/${projectId}/lifecycle`)
        }
      >
        Lifecycle
      </NavSubLink>
      <Permission
        level='project'
        permission={ProjectPermission.VIEW_AUDIT_LOG}
        id={projectId}
      >
        {({ permission }) =>
          permission && (
            <NavSubLink
              icon={<ListIcon />}
              id='audit-log-link'
              to={`/project/${projectId}/audit-log`}
              data-test='audit-log-link'
            >
              Audit Log
            </NavSubLink>
          )
        }
      </Permission>
      {Utils.getFlagsmithHasFeature('segment_change_requests') && (
        <ProjectChangeRequestsLink projectId={projectId} />
      )}
      {!!integrations.length && (
        <NavSubLink
          icon={<LayersIcon />}
          id='integrations-link'
          to={`/project/${projectId}/integrations`}
        >
          Integrations
        </NavSubLink>
      )}
      {projectMetricsTooltipEnabled && (
        <NavSubLink
          icon={<BarChartIcon />}
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
        icon={<CompareIcon />}
        id='compare-link'
        to={`/project/${projectId}/compare`}
      >
        Compare
      </NavSubLink>
      {projectAdmin && Utils.getFlagsmithHasFeature('release_pipelines') && (
        <NavSubLink
          icon={<FlashIcon />}
          id='release-pipelines-link'
          to={`/project/${projectId}/release-pipelines`}
        >
          Pipelines
        </NavSubLink>
      )}
      {projectAdmin && (
        <NavSubLink
          icon={<SettingsIcon />}
          id='project-settings-link'
          to={`/project/${projectId}/settings`}
        >
          Project Settings
        </NavSubLink>
      )}
    </OverflowNav>
  )
}

export default ProjectNavbar
