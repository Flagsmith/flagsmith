import { FC, useMemo, useState } from 'react'
import { Cell, Pie, PieChart, Tooltip } from 'recharts'
import {
  ReleasePipelineOverview,
  ReleasePipelineStageStats,
} from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import PanelSearch from 'components/PanelSearch'
import Icon from 'components/Icon'

interface ReleasePipelineStatsTableProps {
  stats: ReleasePipelineOverview[]
  totalProjects: number
}

const stageColours = [
  '#6C63FF',
  '#0AADDF',
  '#FF9F43',
  '#E74C3C',
  '#9B59B6',
  '#3498DB',
]
const releasedColour = '#27AB95'

type OrgRow = {
  organisation_id: number
  organisation_name: string
  pipeline_count: number
  projects: ProjectRow[]
  total_features: number
  total_released: number
}

type ProjectRow = {
  pipelines: ReleasePipelineOverview[]
  project_id: number
  project_name: string
}

const ReleasePipelineStatsTable: FC<ReleasePipelineStatsTableProps> = ({
  stats,
  totalProjects,
}) => {
  const [expandedOrgs, setExpandedOrgs] = useState<number[]>([])
  const [expandedProjects, setExpandedProjects] = useState<number[]>([])
  const [expandedPipelines, setExpandedPipelines] = useState<number[]>([])

  const toggle = (
    setter: React.Dispatch<React.SetStateAction<number[]>>,
    id: number,
  ) => {
    setter((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const orgRows = useMemo(() => {
    const byOrg: Record<number, OrgRow> = {}

    stats.forEach((pipeline) => {
      if (!byOrg[pipeline.organisation_id]) {
        byOrg[pipeline.organisation_id] = {
          organisation_id: pipeline.organisation_id,
          organisation_name: pipeline.organisation_name,
          pipeline_count: 0,
          projects: [],
          total_features: 0,
          total_released: 0,
        }
      }
      const org = byOrg[pipeline.organisation_id]
      org.total_features += pipeline.total_features
      org.total_released += pipeline.completed_features
      org.pipeline_count++

      let project = org.projects.find(
        (p) => p.project_id === pipeline.project_id,
      )
      if (!project) {
        project = {
          pipelines: [],
          project_id: pipeline.project_id,
          project_name: pipeline.project_name,
        }
        org.projects.push(project)
      }
      project.pipelines.push(pipeline)
    })

    return Object.values(byOrg)
  }, [stats])

  const pipelineCount = stats.length
  const adoptionPct =
    totalProjects > 0 ? Math.round((pipelineCount / totalProjects) * 100) : 0

  const renderStages = (
    stages: ReleasePipelineStageStats[],
    _totalFeatures: number,
    completedFeatures: number,
  ) => {
    // Build pie chart data for this pipeline
    const pieData = [
      ...stages.map((stage, idx) => ({
        colour: stageColours[idx % stageColours.length],
        name: stage.stage_name,
        value: stage.features_in_stage,
      })),
      { colour: releasedColour, name: 'Released', value: completedFeatures },
    ].filter((d) => d.value > 0)

    return (
      <div
        className='d-flex flex-row'
        style={{
          background: '#f4f5f7',
          borderTop: '1px solid #eee',
          paddingBottom: 12,
          paddingTop: 12,
        }}
      >
        {/* Pie chart */}
        <div
          style={{
            alignItems: 'center',
            display: 'flex',
            justifyContent: 'center',
            minWidth: 220,
            paddingLeft: 72,
          }}
        >
          {pieData.length > 0 ? (
            <PieChart width={180} height={180}>
              <Pie
                data={pieData}
                dataKey='value'
                nameKey='name'
                cx='50%'
                cy='50%'
                innerRadius={40}
                outerRadius={75}
                paddingAngle={2}
              >
                {pieData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.colour} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          ) : (
            <div className='text-muted' style={{ fontSize: 12 }}>
              No features yet
            </div>
          )}
        </div>

        {/* Stage list */}
        <div style={{ flex: 1 }}>
          {stages.map((stage, idx) => (
            <div
              key={stage.order}
              className='d-flex flex-row align-items-center'
              style={{ paddingBottom: 6, paddingRight: 20, paddingTop: 6 }}
            >
              <div
                style={{
                  background: stageColours[idx % stageColours.length],
                  borderRadius: 3,
                  height: 10,
                  marginRight: 8,
                  minWidth: 10,
                  width: 10,
                }}
              />
              <div style={{ flex: 1 }}>
                <span className='font-weight-medium' style={{ fontSize: 13 }}>
                  {stage.stage_name}
                </span>
                <div
                  className='text-muted'
                  style={{ fontSize: 11, marginTop: 1 }}
                >
                  {stage.trigger_description} · {stage.action_description}
                </div>
              </div>
              <span
                className='font-weight-medium'
                style={{ fontSize: 13, minWidth: 90, textAlign: 'right' }}
              >
                Features ({stage.features_in_stage})
              </span>
            </div>
          ))}
          <div
            className='d-flex flex-row align-items-center'
            style={{
              borderTop: '1px solid #e0e0e0',
              marginTop: 4,
              paddingRight: 20,
              paddingTop: 8,
            }}
          >
            <div
              style={{
                background: releasedColour,
                borderRadius: 3,
                height: 10,
                marginRight: 8,
                minWidth: 10,
                width: 10,
              }}
            />
            <div style={{ flex: 1 }}>
              <span
                className='font-weight-medium'
                style={{ color: releasedColour, fontSize: 13 }}
              >
                Released
              </span>
              <div
                className='text-muted'
                style={{ fontSize: 11, marginTop: 1 }}
              >
                Features that completed this pipeline
              </div>
            </div>
            <span
              className='font-weight-medium'
              style={{ fontSize: 13, minWidth: 90, textAlign: 'right' }}
            >
              Features ({completedFeatures})
            </span>
          </div>
        </div>
      </div>
    )
  }

  const renderPipelines = (project: ProjectRow) => (
    <div style={{ background: '#f8f9fa', borderTop: '1px solid #eee' }}>
      {project.pipelines.map((pipeline) => {
        const completionPct =
          pipeline.total_features > 0
            ? Math.round(
                (pipeline.completed_features / pipeline.total_features) * 100,
              )
            : 0
        const inFlightTotal = pipeline.stages.reduce(
          (sum, s) => sum + s.features_in_stage,
          0,
        )
        const isExpanded = expandedPipelines.includes(pipeline.pipeline_id)

        return (
          <div key={pipeline.pipeline_id}>
            <div
              className='d-flex flex-row align-items-center clickable'
              onClick={() => toggle(setExpandedPipelines, pipeline.pipeline_id)}
              style={{ paddingBottom: 8, paddingLeft: 72, paddingTop: 8 }}
            >
              <div
                className='flex-fill d-flex align-items-center'
                style={{ gap: 6 }}
              >
                <Icon
                  name={isExpanded ? 'chevron-down' : 'chevron-right'}
                  width={14}
                />
                <span className='font-weight-medium' style={{ fontSize: 13 }}>
                  {pipeline.pipeline_name}
                </span>
                <span
                  style={{
                    background: pipeline.is_published
                      ? '#27AB9518'
                      : '#9DA4AE18',
                    borderRadius: 4,
                    color: pipeline.is_published ? '#27AB95' : '#9DA4AE',
                    fontSize: 10,
                    fontWeight: 600,
                    marginLeft: 4,
                    padding: '1px 5px',
                  }}
                >
                  {pipeline.is_published ? 'Published' : 'Draft'}
                </span>
              </div>
              <div
                className='table-column text-muted'
                style={{ fontSize: 13, width: 100 }}
              >
                {pipeline.stages.length} stages
              </div>
              <div
                className='table-column text-muted'
                style={{ fontSize: 13, width: 100 }}
              >
                {pipeline.total_features} features
                {inFlightTotal > 0 && (
                  <span style={{ fontSize: 11 }}>
                    {' '}
                    ({inFlightTotal} in progress)
                  </span>
                )}
              </div>
              <div
                className='table-column d-flex align-items-center'
                style={{ gap: 6, width: 160 }}
              >
                <div
                  style={{
                    background: '#e9ecef',
                    borderRadius: 4,
                    flex: 1,
                    height: 6,
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      background: (() => {
                        if (completionPct >= 70) return '#27AB95'
                        if (completionPct >= 40) return '#FF9F43'
                        return '#e74c3c'
                      })(),
                      borderRadius: 4,
                      height: '100%',
                      width: `${Math.max(
                        completionPct,
                        pipeline.completed_features > 0 ? 3 : 0,
                      )}%`,
                    }}
                  />
                </div>
                <span
                  className='font-weight-medium'
                  style={{ fontSize: 12, minWidth: 52, whiteSpace: 'nowrap' }}
                >
                  {pipeline.completed_features}/{pipeline.total_features}{' '}
                  released
                </span>
              </div>
            </div>
            {isExpanded &&
              renderStages(
                pipeline.stages,
                pipeline.total_features,
                pipeline.completed_features,
              )}
          </div>
        )
      })}
    </div>
  )

  const renderProjects = (org: OrgRow) => (
    <div style={{ background: '#fafbfc', borderTop: '1px solid #eee' }}>
      {org.projects.map((project) => {
        const isExpanded = expandedProjects.includes(project.project_id)
        const projectPipelineCount = project.pipelines.length
        const projectFeatures = project.pipelines.reduce(
          (sum, p) => sum + p.total_features,
          0,
        )
        const projectReleased = project.pipelines.reduce(
          (sum, p) => sum + p.completed_features,
          0,
        )

        return (
          <div key={project.project_id}>
            <div
              className='d-flex flex-row align-items-center clickable'
              onClick={() => toggle(setExpandedProjects, project.project_id)}
              style={{ paddingBottom: 10, paddingLeft: 48, paddingTop: 10 }}
            >
              <div
                className='flex-fill d-flex align-items-center'
                style={{ gap: 6 }}
              >
                <Icon
                  name={isExpanded ? 'chevron-down' : 'chevron-right'}
                  width={14}
                />
                <span className='font-weight-medium' style={{ fontSize: 13 }}>
                  {project.project_name}
                </span>
                <span className='text-muted' style={{ fontSize: 12 }}>
                  ({projectPipelineCount}{' '}
                  {projectPipelineCount === 1 ? 'pipeline' : 'pipelines'})
                </span>
              </div>
              <div
                className='table-column text-muted'
                style={{ fontSize: 13, width: 120 }}
              >
                {projectFeatures} features
              </div>
              <div
                className='table-column font-weight-medium'
                style={{ color: '#27AB95', fontSize: 13, width: 120 }}
              >
                {projectReleased} released
              </div>
            </div>
            {isExpanded && renderPipelines(project)}
          </div>
        )
      })}
    </div>
  )

  return (
    <div>
      <div className='text-muted mb-3' style={{ fontSize: 13, paddingLeft: 4 }}>
        {pipelineCount} of {totalProjects} projects use release pipelines (
        {adoptionPct}%)
      </div>

      <PanelSearch
        className='no-pad'
        filterRow={(item: OrgRow, search: string) => {
          const q = search.toLowerCase()
          return (
            item.organisation_name.toLowerCase().includes(q) ||
            item.projects.some(
              (p) =>
                p.project_name.toLowerCase().includes(q) ||
                p.pipelines.some((pl) =>
                  pl.pipeline_name.toLowerCase().includes(q),
                ),
            )
          )
        }}
        header={
          <div className='table-header d-flex flex-row align-items-center'>
            <div className='table-column flex-fill' style={{ paddingLeft: 20 }}>
              Organisation
            </div>
            <div className='table-column' style={{ width: 120 }}>
              Pipelines
            </div>
            <div className='table-column' style={{ width: 120 }}>
              Features
            </div>
            <div className='table-column' style={{ width: 120 }}>
              Released
            </div>
          </div>
        }
        id='release-pipeline-stats-table'
        items={orgRows}
        paging={orgRows.length > 10 ? { goToPage: 1, pageSize: 10 } : undefined}
        renderRow={(org: OrgRow) => {
          const isExpanded = expandedOrgs.includes(org.organisation_id)
          const releasedPct =
            org.total_features > 0
              ? Math.round((org.total_released / org.total_features) * 100)
              : 0

          return (
            <div>
              <div
                className='flex-row list-item clickable'
                onClick={() => toggle(setExpandedOrgs, org.organisation_id)}
                style={{ paddingBottom: 12, paddingTop: 12 }}
              >
                <div
                  className='flex-fill d-flex align-items-center'
                  style={{ gap: 8, paddingLeft: 20 }}
                >
                  <Icon
                    name={isExpanded ? 'chevron-down' : 'chevron-right'}
                    width={16}
                  />
                  <span className='font-weight-medium'>
                    {org.organisation_name}
                  </span>
                </div>
                <div
                  className='table-column font-weight-medium'
                  style={{ fontSize: 13, width: 120 }}
                >
                  {org.pipeline_count}
                </div>
                <div
                  className='table-column font-weight-medium'
                  style={{ fontSize: 13, width: 120 }}
                >
                  {org.total_features}
                </div>
                <div
                  className='table-column d-flex align-items-center'
                  style={{ gap: 8, width: 120 }}
                >
                  <span
                    className='font-weight-medium'
                    style={{ color: '#27AB95', fontSize: 13 }}
                  >
                    {org.total_released}
                  </span>
                  <span className='text-muted' style={{ fontSize: 12 }}>
                    ({releasedPct}%)
                  </span>
                </div>
              </div>
              {isExpanded && renderProjects(org)}
            </div>
          )
        }}
        sorting={[
          {
            default: true,
            label: 'Released',
            order: SortOrder.DESC,
            value: 'total_released',
          },
          {
            label: 'Organisation',
            order: SortOrder.ASC,
            value: 'organisation_name',
          },
          {
            label: 'Features',
            order: SortOrder.DESC,
            value: 'total_features',
          },
          {
            label: 'Pipelines',
            order: SortOrder.DESC,
            value: 'pipeline_count',
          },
        ]}
        title='Release Pipeline'
      />
    </div>
  )
}

export default ReleasePipelineStatsTable
