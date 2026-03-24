import React, { FC, useRef, useEffect, useState } from 'react'

interface CollapseProps {
  children: React.ReactNode
  in: boolean
}

const Collapse: FC<CollapseProps> = ({ children, in: open }) => {
  const contentRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState<number | undefined>(
    open ? undefined : 0,
  )

  useEffect(() => {
    if (!contentRef.current) return

    if (open) {
      const contentHeight = contentRef.current.scrollHeight
      setHeight(contentHeight)
      const timer = setTimeout(() => setHeight(undefined), 300)
      return () => clearTimeout(timer)
    } else {
      const contentHeight = contentRef.current.scrollHeight
      setHeight(contentHeight)
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setHeight(0)
        })
      })
    }
  }, [open])

  return (
    <div
      ref={contentRef}
      style={{
        height: height !== undefined ? `${height}px` : 'auto',
        overflow: 'hidden',
        transition: 'height 300ms cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {children}
    </div>
  )
}

export default Collapse
