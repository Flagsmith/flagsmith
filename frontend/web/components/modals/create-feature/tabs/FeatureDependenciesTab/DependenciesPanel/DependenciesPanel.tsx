import { FC, ReactNode } from 'react'
import './DependenciesPanel.scss'

const DependenciesPanel: FC<{ children: ReactNode }> = ({ children }) => (
  <div className='dependencies-panel rounded-md overflow-hidden'>
    {children}
  </div>
)

export default DependenciesPanel
