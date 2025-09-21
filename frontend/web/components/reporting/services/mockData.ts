// Mock data for reporting dashboard development

export interface MetricItem {
  name: string
  description: string
  entity: 'projects' | 'users' | 'environments' | 'features' | 'segments' | 'identities' | 'time'
  value: number
  rank: number
}

export interface ActivityDataPoint {
  date: string
  features_created: number
  features_updated: number
  features_deleted: number
  change_requests_committed: number
}

export interface RecentActivity {
  id: string
  timestamp: string
  action: string
  description: string
  user: string
  project?: string
  environment?: string
}

// Organization-level mock data - Strategic overview metrics
export const mockOrganisationMetrics: MetricItem[] = [
  {
    name: 'total_projects',
    description: 'Projects',
    entity: 'projects',
    value: 8,
    rank: 1
  },
  {
    name: 'total_users',
    description: 'Users',
    entity: 'users',
    value: 156,
    rank: 2
  },
  {
    name: 'total_environments',
    description: 'Environments',
    entity: 'environments',
    value: 24,
    rank: 3
  },
  {
    name: 'total_features',
    description: 'Features',
    entity: 'features',
    value: 342,
    rank: 4
  },
  {
    name: 'total_segments',
    description: 'Segments',
    entity: 'segments',
    value: 67,
    rank: 5
  },
  {
    name: 'total_identities',
    description: 'Identity overrides',
    entity: 'identities',
    value: 124,
    rank: 6
  },
  {
    name: 'unused_features',
    description: 'Unused features',
    entity: 'features',
    value: 23,
    rank: 7
  },
  {
    name: 'stale_features',
    description: 'Stale features',
    entity: 'features',
    value: 18,
    rank: 8
  }
]

// Mock filtered organization data (when specific project selected)
export const mockOrganisationFilteredMetrics: MetricItem[] = [
  {
    name: 'total_projects',
    description: 'Projects',
    entity: 'projects',
    value: 8, // Always shows total projects
    rank: 1
  },
  {
    name: 'total_users',
    description: 'Users',
    entity: 'users',
    value: 24, // Filtered to this project's users
    rank: 2
  },
  {
    name: 'total_environments',
    description: 'Environments',
    entity: 'environments',
    value: 3, // Filtered to this project's environments
    rank: 3
  },
  {
    name: 'total_features',
    description: 'Features',
    entity: 'features',
    value: 42, // Filtered to this project's features
    rank: 4
  },
  {
    name: 'total_segments',
    description: 'Segments',
    entity: 'segments',
    value: 12, // Filtered to this project's segments
    rank: 5
  },
  {
    name: 'total_identities',
    description: 'Identity overrides',
    entity: 'identities',
    value: 28, // Filtered to this project's overrides
    rank: 6
  },
  {
    name: 'unused_features',
    description: 'Unused features',
    entity: 'features',
    value: 4, // Filtered to this project's unused features
    rank: 7
  },
  {
    name: 'stale_features',
    description: 'Stale features',
    entity: 'features',
    value: 3, // Filtered to this project's stale features
    rank: 8
  }
]

// Project-level mock data - Focused tactical metrics
export const mockProjectMetrics: MetricItem[] = [
  {
    name: 'total_features',
    description: 'Features',
    entity: 'features',
    value: 42,
    rank: 1
  },
  {
    name: 'total_environments',
    description: 'Environments',
    entity: 'environments',
    value: 3,
    rank: 2
  },
  {
    name: 'total_segments',
    description: 'Segments',
    entity: 'segments',
    value: 12,
    rank: 3
  },
  {
    name: 'total_identities',
    description: 'Identity overrides',
    entity: 'identities',
    value: 28,
    rank: 4
  },
  {
    name: 'unused_features',
    description: 'Unused features',
    entity: 'features',
    value: 4,
    rank: 5
  },
  {
    name: 'stale_features',
    description: 'Stale features',
    entity: 'features',
    value: 3,
    rank: 6
  }
]

// Mock activity data for organization level (aggregated across all projects)
export const mockOrganisationActivityData: ActivityDataPoint[] = [
  { date: '2024-01-01', features_created: 12, features_updated: 28, features_deleted: 2, change_requests_committed: 8 },
  { date: '2024-01-02', features_created: 8, features_updated: 19, features_deleted: 1, change_requests_committed: 5 },
  { date: '2024-01-03', features_created: 15, features_updated: 34, features_deleted: 3, change_requests_committed: 11 },
  { date: '2024-01-04', features_created: 6, features_updated: 14, features_deleted: 2, change_requests_committed: 3 },
  { date: '2024-01-05', features_created: 10, features_updated: 23, features_deleted: 1, change_requests_committed: 7 },
  { date: '2024-01-06', features_created: 13, features_updated: 29, features_deleted: 2, change_requests_committed: 6 },
  { date: '2024-01-07', features_created: 7, features_updated: 21, features_deleted: 1, change_requests_committed: 9 }
]

// Mock filtered organization data (when specific project selected)
export const mockOrganisationFilteredActivityData: ActivityDataPoint[] = [
  { date: '2024-01-01', features_created: 3, features_updated: 7, features_deleted: 1, change_requests_committed: 2 },
  { date: '2024-01-02', features_created: 2, features_updated: 5, features_deleted: 0, change_requests_committed: 1 },
  { date: '2024-01-03', features_created: 4, features_updated: 8, features_deleted: 1, change_requests_committed: 3 },
  { date: '2024-01-04', features_created: 1, features_updated: 3, features_deleted: 0, change_requests_committed: 1 },
  { date: '2024-01-05', features_created: 3, features_updated: 6, features_deleted: 0, change_requests_committed: 2 },
  { date: '2024-01-06', features_created: 2, features_updated: 7, features_deleted: 1, change_requests_committed: 1 },
  { date: '2024-01-07', features_created: 1, features_updated: 4, features_deleted: 0, change_requests_committed: 2 }
]

// Mock activity data for project level (single project)
export const mockProjectActivityData: ActivityDataPoint[] = [
  { date: '2024-01-01', features_created: 3, features_updated: 7, features_deleted: 1, change_requests_committed: 2 },
  { date: '2024-01-02', features_created: 2, features_updated: 5, features_deleted: 0, change_requests_committed: 1 },
  { date: '2024-01-03', features_created: 4, features_updated: 8, features_deleted: 1, change_requests_committed: 3 },
  { date: '2024-01-04', features_created: 1, features_updated: 3, features_deleted: 0, change_requests_committed: 1 },
  { date: '2024-01-05', features_created: 3, features_updated: 6, features_deleted: 0, change_requests_committed: 2 },
  { date: '2024-01-06', features_created: 2, features_updated: 7, features_deleted: 1, change_requests_committed: 1 },
  { date: '2024-01-07', features_created: 1, features_updated: 4, features_deleted: 0, change_requests_committed: 2 }
]

// Backward compatibility - default to organization data
export const mockActivityData = mockOrganisationActivityData

// Mock recent activity data
export const mockRecentActivities: RecentActivity[] = [
  {
    id: '1',
    timestamp: '2024-01-07T14:30:00Z',
    action: 'feature_created',
    description: 'New feature "Dark Mode Toggle" created',
    user: 'John Doe',
    project: 'Mobile App',
    environment: 'Production'
  },
  {
    id: '2',
    timestamp: '2024-01-07T13:45:00Z',
    action: 'feature_updated',
    description: 'Feature "User Authentication" updated',
    user: 'Jane Smith',
    project: 'Web Dashboard',
    environment: 'Staging'
  },
  {
    id: '3',
    timestamp: '2024-01-07T12:20:00Z',
    action: 'change_request_committed',
    description: 'Change request for "Payment Gateway" committed',
    user: 'Mike Johnson',
    project: 'E-commerce',
    environment: 'Production'
  },
  {
    id: '4',
    timestamp: '2024-01-07T11:15:00Z',
    action: 'feature_updated',
    description: 'Feature "Search Filters" updated',
    user: 'Sarah Wilson',
    project: 'Mobile App',
    environment: 'Development'
  },
  {
    id: '5',
    timestamp: '2024-01-07T10:30:00Z',
    action: 'feature_deleted',
    description: 'Feature "Legacy API" deleted',
    user: 'Tom Brown',
    project: 'Web Dashboard',
    environment: 'Staging'
  }
]

// Mock projects for filtering
export const mockProjects = [
  { id: '1', name: 'Mobile App' },
  { id: '2', name: 'Web Dashboard' },
  { id: '3', name: 'E-commerce' },
  { id: '4', name: 'Admin Panel' },
  { id: '5', name: 'API Gateway' },
  { id: '6', name: 'Analytics Platform' },
  { id: '7', name: 'Customer Portal' },
  { id: '8', name: 'Internal Tools' },
  { id: '9', name: 'Marketing Site' },
  { id: '10', name: 'Mobile Backend' },
  { id: '11', name: 'Data Pipeline' },
  { id: '12', name: 'Notification Service' }
]

// Mock environments for filtering
export const mockEnvironments = [
  { id: '1', name: 'Development' },
  { id: '2', name: 'Staging' },
  { id: '3', name: 'Production' }
]

// Enhanced mock data system that responds to filters
export interface Filters {
  timeRange: {
    startDate: any
    endDate: any
  }
  projectId?: string
  environmentId?: string
}

// Base data for different time periods
const baseDataByTimeRange = {
  '7d': {
    org: { projects: 12, users: 156, environments: 36, features: 450, segments: 120, identities: 180, unused: 45, stale: 32, avgTimeToProd: 14 },
    project: { features: 42, environments: 3, segments: 12, identities: 28, unused: 4, stale: 3, avgTimeToProd: 12 }
  },
  '30d': {
    org: { projects: 12, users: 156, environments: 36, features: 450, segments: 120, identities: 180, unused: 45, stale: 32, avgTimeToProd: 14 },
    project: { features: 42, environments: 3, segments: 12, identities: 28, unused: 4, stale: 3, avgTimeToProd: 12 }
  },
  '90d': {
    org: { projects: 12, users: 156, environments: 36, features: 450, segments: 120, identities: 180, unused: 45, stale: 32, avgTimeToProd: 14 },
    project: { features: 42, environments: 3, segments: 12, identities: 28, unused: 4, stale: 3, avgTimeToProd: 12 }
  }
}

// Project-specific data variations
const projectDataVariations = {
  '1': { // Mobile App
    features: 45, environments: 3, segments: 15, identities: 35, unused: 5, stale: 4, avgTimeToProd: 10,
    activityMultiplier: 1.2
  },
  '2': { // Web Dashboard
    features: 38, environments: 3, segments: 10, identities: 25, unused: 3, stale: 2, avgTimeToProd: 8,
    activityMultiplier: 0.8
  },
  '3': { // E-commerce
    features: 52, environments: 4, segments: 18, identities: 42, unused: 6, stale: 5, avgTimeToProd: 16,
    activityMultiplier: 1.5
  },
  '4': { // Admin Panel
    features: 28, environments: 2, segments: 8, identities: 18, unused: 2, stale: 1, avgTimeToProd: 6,
    activityMultiplier: 0.6
  },
  '5': { // API Gateway
    features: 35, environments: 3, segments: 12, identities: 28, unused: 4, stale: 3, avgTimeToProd: 12,
    activityMultiplier: 1.0
  },
  '6': { // Analytics Platform
    features: 62, environments: 4, segments: 20, identities: 48, unused: 8, stale: 6, avgTimeToProd: 18,
    activityMultiplier: 1.3
  },
  '7': { // Customer Portal
    features: 41, environments: 3, segments: 14, identities: 32, unused: 5, stale: 3, avgTimeToProd: 14,
    activityMultiplier: 0.9
  },
  '8': { // Internal Tools
    features: 24, environments: 2, segments: 6, identities: 15, unused: 2, stale: 1, avgTimeToProd: 5,
    activityMultiplier: 0.5
  },
  '9': { // Marketing Site
    features: 18, environments: 2, segments: 4, identities: 12, unused: 1, stale: 1, avgTimeToProd: 4,
    activityMultiplier: 0.4
  },
  '10': { // Mobile Backend
    features: 39, environments: 3, segments: 13, identities: 30, unused: 4, stale: 3, avgTimeToProd: 11,
    activityMultiplier: 1.1
  },
  '11': { // Data Pipeline
    features: 31, environments: 3, segments: 9, identities: 22, unused: 3, stale: 2, avgTimeToProd: 9,
    activityMultiplier: 0.7
  },
  '12': { // Notification Service
    features: 26, environments: 2, segments: 7, identities: 19, unused: 2, stale: 2, avgTimeToProd: 7,
    activityMultiplier: 0.6
  }
}

// Environment-specific data variations
const environmentDataVariations = {
  '1': { // Development
    activityMultiplier: 0.3
  },
  '2': { // Staging
    activityMultiplier: 0.5
  },
  '3': { // Production
    activityMultiplier: 0.2
  }
}

// Helper function to get time range key
function getTimeRangeKey(timeRange: any): string {
  if (!timeRange?.startDate || !timeRange?.endDate) return '30d'
  
  const start = timeRange.startDate
  const end = timeRange.endDate
  const days = end.diff(start, 'days')
  
  if (days <= 7) return '7d'
  if (days <= 30) return '30d'
  return '90d'
}

// Helper function to get time range multipliers for metrics
function getTimeRangeMultiplier(timeRange: any) {
  if (!timeRange?.startDate || !timeRange?.endDate) {
    return {
      userActivity: 1.0,
      featureActivity: 1.0,
      segmentActivity: 1.0,
      identityActivity: 1.0,
      unusedActivity: 1.0,
      staleActivity: 1.0
    }
  }
  
  const start = timeRange.startDate
  const end = timeRange.endDate
  const days = end.diff(start, 'days')
  
  // Shorter time ranges show more focused/active data
  if (days <= 7) {
    return {
      userActivity: 0.3,    // 30% of users active in last 7 days
      featureActivity: 0.8,  // 80% of features (recent activity)
      segmentActivity: 0.6,  // 60% of segments (recent activity)
      identityActivity: 0.4, // 40% of identities (recent activity)
      unusedActivity: 0.2,   // 20% unused (recent activity shows less unused)
      staleActivity: 0.1     // 10% stale (recent activity shows less stale)
    }
  } else if (days <= 30) {
    return {
      userActivity: 0.6,    // 60% of users active in last 30 days
      featureActivity: 0.9,  // 90% of features (monthly activity)
      segmentActivity: 0.8,  // 80% of segments (monthly activity)
      identityActivity: 0.7, // 70% of identities (monthly activity)
      unusedActivity: 0.5,   // 50% unused (monthly activity)
      staleActivity: 0.3     // 30% stale (monthly activity)
    }
  } else {
    return {
      userActivity: 0.8,    // 80% of users active in longer period
      featureActivity: 1.0,  // 100% of features (longer period)
      segmentActivity: 0.9,  // 90% of segments (longer period)
      identityActivity: 0.85, // 85% of identities (longer period)
      unusedActivity: 0.7,   // 70% unused (longer period shows more unused)
      staleActivity: 0.6     // 60% stale (longer period shows more stale)
    }
  }
}

// Generate realistic activity data based on actual date range
function generateActivityData(timeRange: any, context: 'organisation' | 'project', projectId?: string, environmentId?: string): ActivityDataPoint[] {
  if (!timeRange?.startDate || !timeRange?.endDate) {
    // Fallback to last 7 days
    const endDate = moment()
    const startDate = moment().subtract(7, 'days')
    return generateActivityData({ startDate, endDate }, context, projectId, environmentId)
  }

  const start = timeRange.startDate
  const end = timeRange.endDate
  const days = end.diff(start, 'days')
  
  // Determine data granularity based on time range
  let dataPoints: ActivityDataPoint[] = []
  
  if (days <= 7) {
    // Daily data for 7 days or less
    dataPoints = generateDailyData(start, end, context, projectId, environmentId)
  } else if (days <= 30) {
    // Daily data for up to 30 days
    dataPoints = generateDailyData(start, end, context, projectId, environmentId)
  } else if (days <= 90) {
    // Weekly data for up to 90 days
    dataPoints = generateWeeklyData(start, end, context, projectId, environmentId)
  } else {
    // Monthly data for longer periods
    dataPoints = generateMonthlyData(start, end, context, projectId, environmentId)
  }
  
  return dataPoints
}

// Generate daily activity data with realistic patterns
function generateDailyData(start: any, end: any, context: 'organisation' | 'project', projectId?: string, environmentId?: string): ActivityDataPoint[] {
  const dataPoints: ActivityDataPoint[] = []
  const current = start.clone()
  
  // Base activity levels
  let baseCreated = context === 'organisation' ? 15 : 5
  let baseUpdated = context === 'organisation' ? 35 : 12
  let baseDeleted = context === 'organisation' ? 3 : 1
  let baseCommitted = context === 'organisation' ? 12 : 4
  
  // Apply project multipliers
  if (projectId && projectDataVariations[projectId as keyof typeof projectDataVariations]) {
    const multiplier = projectDataVariations[projectId as keyof typeof projectDataVariations].activityMultiplier
    baseCreated = Math.round(baseCreated * multiplier)
    baseUpdated = Math.round(baseUpdated * multiplier)
    baseDeleted = Math.round(baseDeleted * multiplier)
    baseCommitted = Math.round(baseCommitted * multiplier)
  }
  
  // Apply environment multipliers
  if (environmentId && environmentDataVariations[environmentId as keyof typeof environmentDataVariations]) {
    const multiplier = environmentDataVariations[environmentId as keyof typeof environmentDataVariations].activityMultiplier
    baseCreated = Math.round(baseCreated * multiplier)
    baseUpdated = Math.round(baseUpdated * multiplier)
    baseDeleted = Math.round(baseDeleted * multiplier)
    baseCommitted = Math.round(baseCommitted * multiplier)
  }
  
  while (current.isSameOrBefore(end, 'day')) {
    const dayOfWeek = current.day() // 0 = Sunday, 6 = Saturday
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6
    
    // Weekend activity is typically lower
    const weekendMultiplier = isWeekend ? 0.3 : 1.0
    
    // Add some randomness and realistic patterns
    const randomFactor = 0.7 + Math.random() * 0.6 // 0.7 to 1.3
    
    // Features created (higher on weekdays, lower on weekends)
    const featuresCreated = Math.max(0, Math.round(baseCreated * weekendMultiplier * randomFactor))
    
    // Features updated (more consistent, but still lower on weekends)
    const featuresUpdated = Math.max(0, Math.round(baseUpdated * (0.5 + weekendMultiplier * 0.5) * randomFactor))
    
    // Features deleted (rare, mostly on weekdays)
    const featuresDeleted = Math.max(0, Math.round(baseDeleted * weekendMultiplier * (0.5 + Math.random() * 0.5)))
    
    // Change requests committed (higher on weekdays)
    const changeRequestsCommitted = Math.max(0, Math.round(baseCommitted * weekendMultiplier * randomFactor))
    
    dataPoints.push({
      date: current.format('YYYY-MM-DD'),
      features_created: featuresCreated,
      features_updated: featuresUpdated,
      features_deleted: featuresDeleted,
      change_requests_committed: changeRequestsCommitted
    })
    
    current.add(1, 'day')
  }
  
  return dataPoints
}

// Generate weekly activity data
function generateWeeklyData(start: any, end: any, context: 'organisation' | 'project', projectId?: string, environmentId?: string): ActivityDataPoint[] {
  const dataPoints: ActivityDataPoint[] = []
  const current = start.clone().startOf('week')
  
  // Base weekly activity levels
  let baseCreated = context === 'organisation' ? 80 : 25
  let baseUpdated = context === 'organisation' ? 200 : 60
  let baseDeleted = context === 'organisation' ? 15 : 5
  let baseCommitted = context === 'organisation' ? 60 : 20
  
  // Apply multipliers
  if (projectId && projectDataVariations[projectId as keyof typeof projectDataVariations]) {
    const multiplier = projectDataVariations[projectId as keyof typeof projectDataVariations].activityMultiplier
    baseCreated = Math.round(baseCreated * multiplier)
    baseUpdated = Math.round(baseUpdated * multiplier)
    baseDeleted = Math.round(baseDeleted * multiplier)
    baseCommitted = Math.round(baseCommitted * multiplier)
  }
  
  if (environmentId && environmentDataVariations[environmentId as keyof typeof environmentDataVariations]) {
    const multiplier = environmentDataVariations[environmentId as keyof typeof environmentDataVariations].activityMultiplier
    baseCreated = Math.round(baseCreated * multiplier)
    baseUpdated = Math.round(baseUpdated * multiplier)
    baseDeleted = Math.round(baseDeleted * multiplier)
    baseCommitted = Math.round(baseCommitted * multiplier)
  }
  
  while (current.isSameOrBefore(end, 'week')) {
    const randomFactor = 0.8 + Math.random() * 0.4 // 0.8 to 1.2
    
    dataPoints.push({
      date: current.format('YYYY-MM-DD'),
      features_created: Math.max(0, Math.round(baseCreated * randomFactor)),
      features_updated: Math.max(0, Math.round(baseUpdated * randomFactor)),
      features_deleted: Math.max(0, Math.round(baseDeleted * randomFactor)),
      change_requests_committed: Math.max(0, Math.round(baseCommitted * randomFactor))
    })
    
    current.add(1, 'week')
  }
  
  return dataPoints
}

// Generate monthly activity data
function generateMonthlyData(start: any, end: any, context: 'organisation' | 'project', projectId?: string, environmentId?: string): ActivityDataPoint[] {
  const dataPoints: ActivityDataPoint[] = []
  const current = start.clone().startOf('month')
  
  // Base monthly activity levels
  let baseCreated = context === 'organisation' ? 300 : 100
  let baseUpdated = context === 'organisation' ? 800 : 250
  let baseDeleted = context === 'organisation' ? 60 : 20
  let baseCommitted = context === 'organisation' ? 250 : 80
  
  // Apply multipliers
  if (projectId && projectDataVariations[projectId as keyof typeof projectDataVariations]) {
    const multiplier = projectDataVariations[projectId as keyof typeof projectDataVariations].activityMultiplier
    baseCreated = Math.round(baseCreated * multiplier)
    baseUpdated = Math.round(baseUpdated * multiplier)
    baseDeleted = Math.round(baseDeleted * multiplier)
    baseCommitted = Math.round(baseCommitted * multiplier)
  }
  
  if (environmentId && environmentDataVariations[environmentId as keyof typeof environmentDataVariations]) {
    const multiplier = environmentDataVariations[environmentId as keyof typeof environmentDataVariations].activityMultiplier
    baseCreated = Math.round(baseCreated * multiplier)
    baseUpdated = Math.round(baseUpdated * multiplier)
    baseDeleted = Math.round(baseDeleted * multiplier)
    baseCommitted = Math.round(baseCommitted * multiplier)
  }
  
  while (current.isSameOrBefore(end, 'month')) {
    const randomFactor = 0.7 + Math.random() * 0.6 // 0.7 to 1.3
    
    dataPoints.push({
      date: current.format('YYYY-MM-DD'),
      features_created: Math.max(0, Math.round(baseCreated * randomFactor)),
      features_updated: Math.max(0, Math.round(baseUpdated * randomFactor)),
      features_deleted: Math.max(0, Math.round(baseDeleted * randomFactor)),
      change_requests_committed: Math.max(0, Math.round(baseCommitted * randomFactor))
    })
    
    current.add(1, 'month')
  }
  
  return dataPoints
}

// Generate filtered organization metrics
export function getFilteredOrganisationMetrics(filters: Filters): MetricItem[] {
  const timeRangeKey = getTimeRangeKey(filters.timeRange)
  const baseData = baseDataByTimeRange[timeRangeKey as keyof typeof baseDataByTimeRange]
  
  let metrics = { ...baseData.org }
  
  // Apply time range effects to make metrics more realistic
  const timeRangeMultiplier = getTimeRangeMultiplier(filters.timeRange)
  
  // Apply project filter
  if (filters.projectId && projectDataVariations[filters.projectId as keyof typeof projectDataVariations]) {
    const projectData = projectDataVariations[filters.projectId as keyof typeof projectDataVariations]
    metrics = {
      projects: metrics.projects, // Always show total projects
      users: Math.floor(metrics.users * 0.15), // Filtered users
      environments: projectData.environments,
      features: projectData.features,
      segments: projectData.segments,
      identities: projectData.identities,
      unused: projectData.unused,
      stale: projectData.stale,
      avgTimeToProd: projectData.avgTimeToProd
    }
  }
  
  // Apply time range effects to relevant metrics
  metrics.users = Math.floor(metrics.users * timeRangeMultiplier.userActivity)
  metrics.features = Math.floor(metrics.features * timeRangeMultiplier.featureActivity)
  metrics.segments = Math.floor(metrics.segments * timeRangeMultiplier.segmentActivity)
  metrics.identities = Math.floor(metrics.identities * timeRangeMultiplier.identityActivity)
  metrics.unused = Math.floor(metrics.unused * timeRangeMultiplier.unusedActivity)
  metrics.stale = Math.floor(metrics.stale * timeRangeMultiplier.staleActivity)
  
  return [
    { name: 'total_projects', description: 'Projects', entity: 'projects', value: metrics.projects, rank: 1 },
    { name: 'total_users', description: 'Active Users', entity: 'users', value: metrics.users, rank: 2 },
    { name: 'total_environments', description: 'Environments', entity: 'environments', value: metrics.environments, rank: 3 },
    { name: 'total_features', description: 'Features', entity: 'features', value: metrics.features, rank: 4 },
    { name: 'total_segments', description: 'Segments', entity: 'segments', value: metrics.segments, rank: 5 },
    { name: 'total_identities', description: 'Identity overrides', entity: 'identities', value: metrics.identities, rank: 6 },
    { name: 'unused_features', description: 'Unused features', entity: 'features', value: metrics.unused, rank: 7 },
    { name: 'stale_features', description: 'Stale features', entity: 'features', value: metrics.stale, rank: 8 },
    { name: 'avg_time_to_prod', description: 'Avg time to production (days)', entity: 'time', value: metrics.avgTimeToProd, rank: 9 }
  ]
}

// Generate filtered project metrics
export function getFilteredProjectMetrics(filters: Filters): MetricItem[] {
  const timeRangeKey = getTimeRangeKey(filters.timeRange)
  const baseData = baseDataByTimeRange[timeRangeKey as keyof typeof baseDataByTimeRange]
  
  let metrics = { ...baseData.project }
  
  // Apply time range effects to make metrics more realistic
  const timeRangeMultiplier = getTimeRangeMultiplier(filters.timeRange)
  
  // Apply project-specific variations
  if (filters.projectId && projectDataVariations[filters.projectId as keyof typeof projectDataVariations]) {
    const projectData = projectDataVariations[filters.projectId as keyof typeof projectDataVariations]
    metrics = {
      features: projectData.features,
      environments: projectData.environments,
      segments: projectData.segments,
      identities: projectData.identities,
      unused: projectData.unused,
      stale: projectData.stale,
      avgTimeToProd: projectData.avgTimeToProd
    }
  }
  
  // Apply time range effects to relevant metrics
  metrics.features = Math.floor(metrics.features * timeRangeMultiplier.featureActivity)
  metrics.segments = Math.floor(metrics.segments * timeRangeMultiplier.segmentActivity)
  metrics.identities = Math.floor(metrics.identities * timeRangeMultiplier.identityActivity)
  metrics.unused = Math.floor(metrics.unused * timeRangeMultiplier.unusedActivity)
  metrics.stale = Math.floor(metrics.stale * timeRangeMultiplier.staleActivity)
  
  return [
    { name: 'total_features', description: 'Features', entity: 'features', value: metrics.features, rank: 1 },
    { name: 'total_environments', description: 'Environments', entity: 'environments', value: metrics.environments, rank: 2 },
    { name: 'total_segments', description: 'Segments', entity: 'segments', value: metrics.segments, rank: 3 },
    { name: 'total_identities', description: 'Identity overrides', entity: 'identities', value: metrics.identities, rank: 4 },
    { name: 'unused_features', description: 'Unused features', entity: 'features', value: metrics.unused, rank: 5 },
    { name: 'stale_features', description: 'Stale features', entity: 'features', value: metrics.stale, rank: 6 },
    { name: 'avg_time_to_prod', description: 'Avg time to production (days)', entity: 'time', value: metrics.avgTimeToProd, rank: 7 }
  ]
}

// Performance metrics interface
export interface PerformanceMetrics {
  avgTimeToProduction: number
  featureUtilizationRate: number
  featuresPerWeek: number
}

// Health metrics interface
export interface HealthMetrics {
  unusedFeatures: number
  staleFeatures: number
}

// Get performance metrics based on context and filters
export function getPerformanceMetrics(filters: Filters, context: 'organisation' | 'project'): PerformanceMetrics {
  let metrics: any
  
  if (context === 'organisation') {
    // Use organization-level data
    const baseData = baseDataByTimeRange['30d'].org
    const timeRangeMultiplier = getTimeRangeMultiplier(filters.timeRange)
    
    metrics = {
      avgTimeToProduction: baseData.avgTimeToProd,
      featureUtilizationRate: Math.floor(100 - (baseData.unused / baseData.features * 100)), // Calculate utilization
      featuresPerWeek: Math.round((baseData.features / 52) * (timeRangeMultiplier.featureActivity || 1)) // Features per week
    }
  } else {
    // Use project-level data
    const projectId = filters.projectId || '1'
    const projectData = projectDataVariations[projectId as keyof typeof projectDataVariations] || projectDataVariations['1']
    const timeRangeMultiplier = getTimeRangeMultiplier(filters.timeRange)
    
    metrics = {
      avgTimeToProduction: projectData.avgTimeToProd,
      featureUtilizationRate: Math.floor(100 - (projectData.unused / projectData.features * 100)), // Calculate utilization
      featuresPerWeek: Math.round((projectData.features / 52) * (timeRangeMultiplier.featureActivity || 1)) // Features per week
    }
  }
  
  return metrics
}

// Get health metrics based on context and filters
export function getHealthMetrics(filters: Filters, context: 'organisation' | 'project'): HealthMetrics {
  let metrics: any
  
  if (context === 'organisation') {
    // Use organization-level data
    const baseData = baseDataByTimeRange['30d'].org
    const timeRangeMultiplier = getTimeRangeMultiplier(filters.timeRange)
    
    metrics = {
      unusedFeatures: Math.floor(baseData.unused * (timeRangeMultiplier.unusedActivity || 1)),
      staleFeatures: Math.floor(baseData.stale * (timeRangeMultiplier.staleActivity || 1))
    }
  } else {
    // Use project-level data
    const projectId = filters.projectId || '1'
    const projectData = projectDataVariations[projectId as keyof typeof projectDataVariations] || projectDataVariations['1']
    const timeRangeMultiplier = getTimeRangeMultiplier(filters.timeRange)
    
    metrics = {
      unusedFeatures: Math.floor(projectData.unused * (timeRangeMultiplier.unusedActivity || 1)),
      staleFeatures: Math.floor(projectData.stale * (timeRangeMultiplier.staleActivity || 1))
    }
  }
  
  return metrics
}

// Generate filtered activity data
export function getFilteredActivityData(filters: Filters, context: 'organisation' | 'project'): ActivityDataPoint[] {
  // Use the new realistic data generation system
  return generateActivityData(filters.timeRange, context, filters.projectId, filters.environmentId)
}
