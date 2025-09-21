import { useState, useEffect } from 'react'

export type ProjectStaticMetrics = {
  features: number
  environments: number
  segments: number
  identityOverrides: number
}

export const useProjectStaticMetrics = (projectId: string) => {
  const [data, setData] = useState<ProjectStaticMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Simulate API call with mock data
    const fetchMetrics = async () => {
      setIsLoading(true)
      try {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // Mock data for project metrics
        const mockMetrics: ProjectStaticMetrics = {
          features: 23,
          environments: 3,
          segments: 8,
          identityOverrides: 45
        }
        
        setData(mockMetrics)
      } catch (err) {
        setError(err as Error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchMetrics()
  }, [projectId])

  return {
    data,
    isLoading,
    error,
  }
}