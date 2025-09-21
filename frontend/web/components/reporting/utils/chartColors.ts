/**
 * Theme-aware chart color utilities
 * 
 * This utility provides colors that automatically adapt to light/dark mode
 * by using CSS custom properties that are defined in the SCSS files.
 */

export const getChartColors = () => {
  // Get computed styles to access CSS custom properties
  const root = document.documentElement
  const computedStyle = getComputedStyle(root)
  
  // Check if dark mode is active
  const isDarkMode = document.body.classList.contains('dark')
  
  return {
    // Grid and axis colors
    grid: isDarkMode ? '#2d3443' : '#eff1f4', // $bg-dark300 : $bg-light300
    axisLine: isDarkMode ? '#2d3443' : '#eff1f4', // $bg-dark300 : $bg-light300
    
    // Text colors
    axisText: isDarkMode ? '#9da4ae' : '#656d7b', // $text-icon-light-grey : $text-icon-grey
    tickText: isDarkMode ? '#ffffff' : '#1a2634', // $text-icon-light : $body-color
    
    // Chart data colors (semantic colors that work in both themes)
    primary: isDarkMode ? '#906af6' : '#6837fc', // $primary400 : $primary
    secondary: isDarkMode ? '#a78bfa' : '#8b5cf6', // Lighter purple for dark mode
    tertiary: isDarkMode ? '#c4b5fd' : '#a78bfa', // Even lighter purple
    quaternary: isDarkMode ? '#ddd6fe' : '#c4b5fd', // Lightest purple
    
    // Utility colors
    success: isDarkMode ? '#56ccad' : '#27ab95', // $success400 : $success
    warning: isDarkMode ? '#ffb84d' : '#ff9f43', // $warning (lighter for dark mode)
    danger: isDarkMode ? '#f57c78' : '#ef4d56', // $danger400 : $danger
    info: isDarkMode ? '#4dd4f7' : '#0aaddf', // $info (lighter for dark mode)
  }
}

/**
 * Get theme-aware chart configuration for Recharts components
 */
export const getChartConfig = () => {
  const colors = getChartColors()
  
  return {
    // CartesianGrid props
    gridProps: {
      stroke: colors.grid,
      vertical: false
    },
    
    // XAxis props
    xAxisProps: {
      axisLine: { stroke: colors.axisLine },
      tickLine: false,
      tick: { 
        fill: colors.axisText, 
        fontSize: 12 
      }
    },
    
    // YAxis props  
    yAxisProps: {
      axisLine: { stroke: colors.axisLine },
      tickLine: false,
      tick: { 
        fill: colors.tickText, 
        fontSize: 12 
      }
    }
  }
}

/**
 * Get a color palette for chart data series
 */
export const getChartColorPalette = (count: number = 4) => {
  const colors = getChartColors()
  
  const palette = [
    colors.primary,
    colors.secondary, 
    colors.tertiary,
    colors.quaternary,
    colors.success,
    colors.warning,
    colors.danger,
    colors.info
  ]
  
  // Return as many colors as requested, cycling through the palette
  return Array.from({ length: count }, (_, i) => palette[i % palette.length])
}
