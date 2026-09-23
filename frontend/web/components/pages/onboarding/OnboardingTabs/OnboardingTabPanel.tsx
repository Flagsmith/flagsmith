import React, { FC, ReactNode } from 'react'

export type OnboardingTabPanelProps = {
  // Must match the id of the tab that controls this panel.
  tabId: string
  active: boolean
  className?: string
  children: ReactNode
}

// Panel half of the tab pattern. Rendered only when active and wired back to
// its tab by id (role/aria-labelledby) so the relationship is announced. It is
// deliberately NOT focusable (no tabIndex): the panel holds focusable controls
// (SDK chips, Copy buttons), so per the WAI-ARIA tabs pattern Tab moves to the
// first control rather than the panel container.
const OnboardingTabPanel: FC<OnboardingTabPanelProps> = ({
  active,
  children,
  className,
  tabId,
}) =>
  active ? (
    <div
      id={`${tabId}-panel`}
      role='tabpanel'
      aria-labelledby={tabId}
      className={className}
    >
      {children}
    </div>
  ) : null

export default OnboardingTabPanel
