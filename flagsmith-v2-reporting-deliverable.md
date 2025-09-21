# V2 Reporting Dashboard - Technical Design Document

**Epic:** Reporting on Feature Management Program #6001  
**Engineer:** Talisson Costa  
**Date:** September 22, 2025  

---

## 📋 Executive Summary

This document outlines the design and implementation approach for Flagsmith's V2 Reporting Dashboard, addressing the need for engineering teams to measure the success of their feature management programs.

**Key Discovery:** After stakeholder clarification, the dashboard should be **organization-level** with project/environment filtering capabilities, solving the discoverability challenge of making org-level insights accessible to project-focused users.

**Implementation Status:** - All frontend components built, committed, and ready for backend integration.

---

## 🔍 Problem Analysis

### Current State
- V1 analytics focuses on API usage (flags, identities, traits)
- Engineering teams lack visibility into feature management program effectiveness  
- No organization-level feature management metrics
- Users primarily work at project level but need org-wide insights
- **Discovery**: Project Settings > Usage tab shows minimal reporting pattern exists but lacks program-level insights

### User Need
> *"Engineering teams using Flagsmith for their feature management programs want to be able to see information on the success of the program."*

### Key Challenge: Discoverability
**Problem:** Organization-level features are typically hidden in "Organization Settings", but reporting is an active feature users need to easily access.

**User Mental Model:** Users think "project-first" but need "organization-level" insights.

**Pattern Discovery:** Analysis revealed existing minimal reporting patterns:
- Project Settings > Usage tab (Features: 0/400, Segments: 0/100) 
- Features page Summary section (Total features: 2, Features enabled: 1, Segment overrides: 0, Identity overrides: 0)

These basic metrics indicate opportunity to consolidate into comprehensive reporting rather than scatter similar data across multiple locations.

### Success Criteria
- Organization-level dashboard with project/environment filtering
- Multiple discoverable entry points (org nav + project context)
- Smart defaults based on user context
- Provide feature management KPIs using available platform data
- Support filtering by time period, project, and environment
- **Build on existing patterns**: Expand Project Settings > Usage tab approach rather than create new patterns
- **Future Enhancement**: Advanced filtering by tags, user groups, and individual users for detailed analysis

---

## 🛠 Technical Discovery

### Current Usage Tab Analysis

**Current "Usage" Tab (Project Settings)**
- **Location:** Project Settings → Usage tab
- **Current Content:** 
  - Features: 0/400
  - Segments: 0/100  
  - Segment Overrides: 0/100
- **Purpose:** Shows project-level usage limits and current usage
- **User Value:** Limited - only shows counts vs limits

**Migration Strategy:**
- **Phase 1:** Keep existing Usage tab and Features Summary, add reporting as new "Project Insights" tab
- **Phase 2:** Enhance reporting with comprehensive metrics and usage limit context
- **Phase 3:** Consolidate scattered metrics - replace Usage tab and Features Summary with unified reporting dashboard

### Data Sources Analysis

**✅ Available Data (Organization-Level Aggregation)**
```
Static Metrics (Organization-wide):
- num_projects: Project.objects.filter(organisation=org).count()
- num_users: UserOrganisation.objects.filter(organisation=org).count()
- num_environments: Environment.objects.filter(project__organisation=org).count()
- num_segments: Segment.objects.filter(project__organisation=org).count()
- num_identity_overrides: Identity.objects.filter(environment__project__organisation=org).count()

Time-Series Metrics (Filterable by Project/Environment):
- features_created: AuditLog → "New Flag / Remote Config created"
- features_updated: AuditLog → "Flag / Remote Config updated" 
- features_deleted: AuditLog → "Flag / Remote Config Deleted"
- change_requests_committed: AuditLog → "Change Request...committed"
```

**🔄 Future Enhancements (Requires New Logic)**
```
- num_stale_features: Requires versioning analysis
- unused_feature_flags: Correlate Feature list with usage data
- avg_time_to_production: Complex audit log parsing
```

### Infrastructure Assessment

**Existing Systems to Leverage:**
- **Organization Navigation**: `OrganisationNavbar.tsx` with Usage, Settings, etc.
- **Organization Usage**: `OrganisationUsagePage` and `useGetOrganisationUsageQuery` patterns
- **Environment Metrics**: `EnvironmentMetricsViewSet` pattern for metrics structure
- **Permissions**: Organization-level permission system in place
- **Styling**: Material-UI + custom Flagsmith components
- **Data Layer**: AuditLog with rich change history
- **Charts**: Recharts library already integrated

---

## 🎨 User Experience Design

### Modular Architecture Strategy

**Dual-Level Approach:**
```
Organization Level (Full Dashboard):
┌─────────────────────────────────────────────────┐
│ Projects | Users | Usage | Reporting | Settings │
└─────────────────────────────────────────────────┘
└── Shows: All projects, org-wide metrics, cross-project insights

Project Level (Focused Metrics):
┌─────────────────────────────────────────────────┐
│ Features | Segments | Identities | Project Insights │
└─────────────────────────────────────────────────┘
└── Shows: Project-specific metrics, filtered org data
```

**Modular Component Strategy:**
- **Shared Components**: Metrics cards, charts, filters, activity lists
- **Context Providers**: Organization vs Project data sources
- **Smart Routing**: Same components, different data contexts
- **Progressive Enhancement**: Project view can link to org view for broader context

### Information Architecture

**Clean, Monochromatic Design with Tabbed Interface:**

**Organization Level (Strategic Overview):**
```
┌─────────────────────────────────────────────────┐
│ [📊 Overview] [📈 Activity] [⚡ Performance] [🔍 Health] │
├─────────────────────────────────────────────────┤
│ Filters                                         │
│ Filter organization-wide metrics by time,      │
│ project, and environment                        │
├─────────────────────────────────────────────────┤
│ Time Range: [Last 30 days] (all metrics)       │
│ Project: [All ▼] (focus on specific project)   │
│ Environment: [All ▼] (select project first)    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Tab Content (changes based on selection)        │
│                                                 │
│ Overview Tab:                                   │
│ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐│
│ │  8  │ 156 │ 24  │ 342 │ 67  │ 124 │ 23  │ 18  ││
│ │ Proj│Users│ Env │ Feat│ Seg │ IdOv│Unused│Stale││
│ └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘│
│                                                 │
│ Activity Tab:                                   │
│ ┌─────────────────────────────────────────────────┐│
│ │ Activity Summary        │ Activity Trends       ││
│ │ Feature activity over   │ Feature activity over ││
│ │ the selected time period│ time                  ││
│ ├─────────┬─────────┬─────┼───────────────────────┤│
│ │   71    │  168    │ 12  │    [Stacked Bar      ││
│ │ Created │ Updated │Del │    Chart showing      ││
│ └─────────┴─────────┴─────┤    daily activity]   ││
│                           └───────────────────────┘│
│                                                 │
│ Performance Tab:                                │
│ ┌─────────────────────────────────────────────────┐│
│ │ Feature Adoption Rate: 89%                     ││
│ │ Average Response Time: 2.3s                    ││
│ │ Uptime: 99.9%                                  ││
│ └─────────────────────────────────────────────────┘│
│                                                 │
│ Health Tab:                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ Unused Features: 23 (with progress bar)        ││
│ │ Stale Features: 18 (with progress bar)         ││
│ │ Recommendations for optimization               ││
│ └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

**Project Level (Focused Tactical):**
```
┌─────────────────────────────────────────────────┐
│ [📊 Overview] [📈 Activity] [⚡ Performance] [🔍 Health] │
├─────────────────────────────────────────────────┤
│ Filters                                         │
│ Filter project metrics by time and environment │
├─────────────────────────────────────────────────┤
│ Time Range: [Last 30 days] (all metrics)       │
│ Environment: [All ▼] (filter by environment)   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Tab Content (project-specific data)             │
│                                                 │
│ Overview Tab:                                   │
│ ┌─────┬─────┬─────┬─────┬─────┬─────┐           │
│ │ 42  │ 3   │ 12  │ 28  │ 4   │ 3   │           │
│ │ Feat│ Env │ Seg │ IdOv│Unused│Stale│           │
│ └─────┴─────┴─────┴─────┴─────┴─────┘           │
│                                                 │
│ Activity Tab:                                   │
│ ┌─────────────────────────────────────────────────┐│
│ │ Activity Summary        │ Activity Trends       ││
│ │ Feature activity over   │ Feature activity over ││
│ │ the selected time period│ time                  ││
│ ├─────────┬─────────┬─────┼───────────────────────┤│
│ │   16    │   40    │  3  │    [Stacked Bar      ││
│ │ Created │ Updated │Del │    Chart showing      ││
│ └─────────┴─────────┴─────┤    daily activity]   ││
│                           └───────────────────────┘│
│                                                 │
│ Performance Tab:                                │
│ ┌─────────────────────────────────────────────────┐│
│ │ Feature Adoption Rate: 92%                     ││
│ │ Average Response Time: 1.8s                    ││
│ │ Uptime: 99.8%                                  ││
│ └─────────────────────────────────────────────────┘│
│                                                 │
│ Health Tab:                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ Unused Features: 4 (with progress bar)         ││
│ │ Stale Features: 3 (with progress bar)          ││
│ │ Project-specific recommendations               ││
│ └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

**Rationale:** 
- Organization-level view with smart filtering
- Multiple entry points for discoverability
- Context-aware defaults based on user journey
- Progressive disclosure from org → project → environment

### Modular Component Architecture

**Shared Components (Reusable):**
```
components/reporting/
├── MetricsOverview.tsx                    // Generic metrics cards
├── ActivityMetrics.tsx                    // Time-filtered metrics + charts
├── ProjectEnvironmentFilters.tsx          // Filtering controls
├── FeatureVelocityChart.tsx               // Recharts implementation
├── RecentActivityList.tsx                 // Audit log feed
└── hooks/
    ├── useReportingMetrics.ts             // Generic metrics hook
    └── useReportingFilters.ts             // Generic filtering logic
```

**Context-Specific Pages:**
```
OrganisationReportingPage.tsx              // Org-level container
├── Uses MetricsOverview (org data)
├── Uses ActivityMetrics (org data)
└── Uses ProjectEnvironmentFilters (org context)

ProjectReportingPage.tsx                   // Project-level container  
├── Uses MetricsOverview (project data)
├── Uses ActivityMetrics (project data)
└── Uses ProjectEnvironmentFilters (project context)
```

**Data Layer (Context Providers):**
```
hooks/
├── useOrganisationMetrics.ts              // Org-level data source
├── useProjectMetrics.ts                   // Project-level data source
└── useReportingMetrics.ts                 // Generic interface
```

**Navigation Integration:**
```
OrganisationNavbar.tsx                     // "Reporting" tab
ProjectNavbar.tsx                          // "Project Insights" tab
```

**Modular Benefits:**
- **Code Reuse**: Same components, different data contexts
- **Consistent UX**: Identical interface at both levels
- **Maintainability**: Single source of truth for UI components
- **Flexibility**: Easy to add new contexts (environment-level, team-level)

---

## ⚙️ Technical Implementation

### Frontend Architecture

**Modular Page Structure:**
```typescript
// Shared Components (Reusable)
const MetricsOverview: FC<MetricsOverviewProps> = ({ 
  context, // 'organisation' | 'project'
  contextId, 
  filters 
}) => {
  const { data: metrics } = useReportingMetrics(context, contextId, filters)
  
  return (
    <div className='metrics-grid'>
      {metrics.map(metric => (
        <MetricCard key={metric.name} {...metric} />
      ))}
    </div>
  )
}

// Organization-Level Page
const OrganisationReportingPage: FC = () => {
  const { organisationId } = useParams()
  const [filters, setFilters] = useState({
    timeRange: '30d',
    projectId: null,
    environmentId: null
  })

  return (
    <div className='app-container container'>
      <PageTitle title='Feature Management Reporting'>
        Organization-wide analytics and insights
      </PageTitle>
      
      <ProjectEnvironmentFilters 
        context="organisation"
        contextId={organisationId}
        filters={filters}
        onFiltersChange={setFilters}
      />
      
      <MetricsOverview 
        context="organisation"
        contextId={organisationId}
        filters={filters}
      />
      
      <ActivityMetrics 
        context="organisation"
        contextId={organisationId}
        filters={filters}
      />
    </div>
  )
}

// Project-Level Page
const ProjectReportingPage: FC = () => {
  const { projectId } = useParams()
  const [filters, setFilters] = useState({
    timeRange: '30d',
    projectId: projectId, // Default to current project
    environmentId: null
  })

  return (
    <div className='app-container container'>
      <PageTitle title='Project Insights'>
        Project-specific analytics and insights
      </PageTitle>
      
      <ProjectEnvironmentFilters 
        context="project"
        contextId={projectId}
        filters={filters}
        onFiltersChange={setFilters}
      />
      
      <MetricsOverview 
        context="project"
        contextId={projectId}
        filters={filters}
      />
      
      <ActivityMetrics 
        context="project"
        contextId={projectId}
        filters={filters}
      />
      
      <div className='mt-4'>
        <Link to={`/organisation/${organisationId}/reporting?project=${projectId}`}>
          View Organization-wide Context →
        </Link>
      </div>
    </div>
  )
}
```

**Generic API Integration:**
```typescript
// Generic metrics hook
const useReportingMetrics = (context: 'organisation' | 'project', contextId: string, filters: Filters) => {
  if (context === 'organisation') {
    return useGetOrganisationMetricsQuery({ organisationId: contextId, ...filters })
  } else {
    return useGetProjectMetricsQuery({ projectId: contextId, ...filters })
  }
}
```

### Backend Implementation Strategy

**Approach:** Leverage existing API patterns and extend current metrics infrastructure.

**Key Backend Considerations:**
- Extend existing `EnvironmentMetricsViewSet` pattern for consistency
- Utilize current `AuditLog` data for activity metrics
- Follow established organization/project permission patterns
- Build on existing caching and performance optimizations

**Implementation Notes:**
- Backend development will follow the modular frontend approach
- API endpoints will mirror the dual-level architecture (org + project)
- Focus on reusing existing data sources and query patterns
- Detailed backend implementation will be addressed in subsequent phases

### Advanced Filtering Strategy (Future Enhancement)

**Rationale for Deferred Implementation:**
- **User Experience**: Keep initial interface simple and focused
- **Progressive Enhancement**: Build core functionality first, add complexity later
- **Learning Curve**: Allow users to understand basic metrics before advanced filtering
- **Development Velocity**: Faster initial delivery with clear enhancement path

**Planned Advanced Filters:**

**Tag-Based Filtering:**
- **Organization Level**: Filter activity data by feature tags (not org metrics)
- **Project Level**: Filter all project metrics by feature tags
- **Use Cases**: Team-specific features, feature categorization, health status filtering

**User Group Filtering:**
- **Activity Attribution**: Filter activity by user permission groups
- **Team Analysis**: Compare feature velocity across different teams
- **Permission Insights**: Understand which groups are most active

**Individual User Filtering:**
- **Activity Tracking**: Filter activity by specific users
- **Individual Performance**: Track individual contributor activity
- **Accountability**: See who created/updated specific features

**Technical Implementation (Future):**
- Leverage existing `TagFilter`, `ConnectedGroupSelect`, and `UserSelect` components
- Extend current filter interface with conditional advanced filters
- Implement smart data filtering logic based on filter type and context
- Add progressive disclosure UI for advanced filtering options

---

---

## 🚀 Implementation Roadmap

### Phase 1: Frontend Foundation (Week 1-2) - **✅ COMPLETED**
**Deliverable:** Reusable frontend reporting system with mock data for rapid prototyping

**✅ Completed:**
- [x] Analyzed existing patterns (EnvironmentMetricsViewSet, OrganisationUsagePage)
- [x] Identified discoverability challenge and solutions
- [x] Designed modular architecture with dual-level support
- [x] Created technical design document with stakeholder alignment
- [x] Planned shared component strategy for code reuse
- [x] Built monochromatic UI design with existing component reuse
- [x] Implemented ProjectEnvironmentFilters using existing ProjectFilter/EnvironmentFilter
- [x] Created modular component architecture (MetricsOverview, ActivityMetrics, etc.)
- [x] **Complete navigation integration for both levels**
- [x] **Finalize cross-level navigation links**
- [x] **Test component integration and routing**
- [x] **Replace all hardcoded colors with semantic CSS classes**
- [x] **Implement theme-aware styling with dark mode support**
- [x] **Create reusable EmptyState component**
- [x] **Extend DateSelect component for flexibility**
- [x] **Commit all changes with proper Conventional Commits**

**📋 Phase 1 Success Criteria:**
- **Organization Level**: Full dashboard accessible from org navigation
- **Project Level**: Focused metrics accessible from project navigation
- **Shared Components**: Same UI components work for both contexts
- **Smart Filtering**: Context-aware defaults and cross-level navigation
- **Component Reuse**: Leveraging existing Flagsmith components (ProjectFilter, EnvironmentFilter, Select)
- **Mock Data**: Functional frontend with realistic mock data for demonstration

**🎯 Phase 1 Implementation Steps:**
1. **Frontend Components** - Build reusable MetricsOverview, ActivityMetrics, Filters
2. **Component Reuse** - Leverage existing ProjectFilter, EnvironmentFilter, SearchableSelect
3. **Mock Data Layer** - Create realistic mock data for rapid development
4. **Dual Navigation** - Add "Reporting" to org nav, "Project Insights" to project nav
5. **Cross-Level Links** - Enable navigation between org and project views
6. **Backend Integration** - Replace mock data with real API calls in future phases

### Phase 2: Backend Integration (Week 3-4)  
**Deliverable:** Replace mock data with real API integration

- [ ] Implement backend metrics services following existing patterns
- [ ] Create organization and project metrics endpoints
- [ ] Integrate real AuditLog data for activity metrics
- [ ] Add proper error handling and loading states
- [ ] Performance optimization and caching

### Phase 3: Advanced Analytics (Future)
**Deliverable:** Sophisticated feature management insights

- [ ] Time-series charts with Recharts integration
- [ ] **Advanced Filtering**: Tags, user groups, and individual user filtering for detailed analysis
- [ ] Stale feature detection and alerts
- [ ] Team productivity metrics and insights
- [ ] **Enhanced Activity Attribution**: Filter activity by who performed actions and when

### Usage Tab Migration Strategy

**Current State:**
- Project Settings → Usage tab shows basic limits (Features: 0/400, Segments: 0/100)
- Limited user value - only shows counts vs limits
- No program-level insights

**Migration Plan:**

**Phase 1.5: Enhanced Usage Context**
- [ ] Add usage limit context to reporting dashboard
- [ ] Show current usage vs limits in Overview tab
- [ ] Add usage trend analysis in Performance tab

**Phase 2: Usage Tab Replacement**
- [ ] Replace "Usage" tab with "Insights" tab
- [ ] Move usage limits to reporting dashboard
- [ ] Add program-level metrics alongside usage data
- [ ] Maintain backward compatibility during transition

**Phase 3: Comprehensive Reporting**
- [ ] Full integration of usage + program metrics
- [ ] Advanced usage analytics (trends, projections, alerts)
- [ ] Usage-based recommendations and optimization

**Benefits of Migration:**
- **Better UX**: Single location for all project insights
- **Enhanced Value**: Usage data + program metrics in one view
- **Reduced Navigation**: Eliminates need to switch between tabs
- **Contextual Insights**: Usage limits shown alongside actual usage patterns
- **Consolidated Metrics**: Remove scattered summary sections (Features page, Usage tab) in favor of comprehensive reporting

---

## 🎯 Success Metrics

### User Adoption
- Dashboard page views vs. current feature usage
- Time spent on reporting vs. other project pages  
- Filter usage patterns

### Business Value
- Engineering teams can quantify feature program success
- Managers gain visibility into feature velocity
- Data-driven optimization of feature management processes

### Technical Success  
- <200ms page load times (leverage existing caching)
- Zero impact on existing V1 analytics performance
- 80%+ code reuse from existing UI patterns
- Seamless integration with current permission system

---

## 🔧 Risk Mitigation

### Low Risk Approach
- **No schema changes** - uses existing data structures
- **Extends existing patterns** - follows established codebase conventions  
- **Incremental delivery** - working foundation first, advanced features later
- **Backward compatibility** - no impact on existing functionality

### Deployment Strategy
- Feature flag gated (`project_metrics_enabled`)
- Gradual rollout by organization
- Easy rollback if issues arise
- Monitoring through existing analytics infrastructure

---

## 📊 Expected Outcomes

**Immediate Value (Phase 1):**
- Engineers can see project structure at a glance
- 404 error resolved → positive user experience
- Foundation for future analytics enhancements

**Medium-term Impact (Phase 2):**
- Feature velocity visibility enables process optimization
- Activity trends help teams understand development patterns
- Audit trail provides accountability and insights

**Long-term Vision (Phase 3):**
- Comprehensive feature management program analytics
- **Advanced Filtering**: Tag-based, user group, and individual user filtering for granular analysis
- Predictive insights for feature success
- Team productivity optimization recommendations
- **Activity Attribution**: Detailed tracking of who is creating, updating, and managing features

---

## 🔍 Strategic Analysis: Component Consistency & Code Duplication

### **Key Questions for Engineering Teams:**

#### **Primary Question:**
> **"How do you keep consistency across features and avoid code duplication or component misuse?"**

#### **Additional Strategic Questions:**

1. **Component Discoverability:**
   > **"How do developers discover existing UI patterns and components when building new features?"**
   - Do you have a component library or documentation?
   - How do new developers learn about existing patterns?

2. **Technical Debt Management:**
   > **"How do you identify and address technical debt in UI components across the platform?"**
   - Do you track hardcoded values (colors, styles) across the codebase?
   - How do you ensure dark mode compatibility across all components?

3. **Pattern Standardization:**
   > **"How do you decide when to create new components versus reusing existing ones?"**
   - Who makes decisions about component creation vs reuse?
   - How do you ensure similar functionality uses consistent patterns?
   - What guidelines exist for component design and usage?

4. **Developer Experience:**
   > **"What tools and processes help developers build consistent, maintainable UI components?"**
   - Do you use linting rules to enforce consistency?
   - How do you onboard new developers to UI patterns?
   - What feedback mechanisms exist for improving developer experience?


---

