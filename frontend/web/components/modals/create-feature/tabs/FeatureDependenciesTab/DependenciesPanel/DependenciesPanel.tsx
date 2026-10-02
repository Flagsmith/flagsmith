import { FC, ReactNode } from 'react'
import './DependenciesPanel.scss'

// The bordered box both halves of the tab draw their contents in.
const DependenciesPanel: FC<{ children: ReactNode }> = ({ children }) => (
  <div className='dependencies-panel'>{children}</div>
)

export default DependenciesPanel
