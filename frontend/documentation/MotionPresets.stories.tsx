import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import { motion, AnimatePresence } from 'motion/react'
import {
  fadeIn,
  slideInRight,
  slideInUp,
  staggerContainer,
  staggerItem,
  springBounce,
  shakeX,
  badgeEntrance,
  pageCrossfade,
} from 'common/utils/motion'

const meta: Meta = {
  tags: ['autodocs'],
  title: 'Design System/Motion Presets',
}
export default meta

type Story = StoryObj

const DemoBox = ({
  children,
  style,
}: {
  children: React.ReactNode
  style?: React.CSSProperties
}) => (
  <div
    style={{
      alignItems: 'center',
      background: 'var(--color-surface-subtle)',
      border: '1px solid var(--color-border-default)',
      borderRadius: 'var(--radius-lg)',
      display: 'flex',
      fontSize: 'var(--font-body-sm-size)',
      justifyContent: 'center',
      padding: '24px 32px',
      ...style,
    }}
  >
    {children}
  </div>
)

export const FadeIn: Story = {
  decorators: [
    () => {
      const [key, setKey] = useState(0)
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <button
            className='btn btn-primary btn-sm'
            onClick={() => setKey((k) => k + 1)}
          >
            Replay
          </button>
          <motion.div
            key={key}
            variants={fadeIn()}
            initial='hidden'
            animate='visible'
          >
            <DemoBox>fadeIn()</DemoBox>
          </motion.div>
          <code style={{ color: 'var(--color-text-secondary)', fontSize: 12 }}>
            {'variants={fadeIn()} initial="hidden" animate="visible"'}
          </code>
        </div>
      )
    },
  ],
}

export const SlideInRight: Story = {
  decorators: [
    () => {
      const [key, setKey] = useState(0)
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <button
            className='btn btn-primary btn-sm'
            onClick={() => setKey((k) => k + 1)}
          >
            Replay
          </button>
          <motion.div
            key={key}
            variants={slideInRight}
            initial='hidden'
            animate='visible'
          >
            <DemoBox>slideInRight — page transitions</DemoBox>
          </motion.div>
        </div>
      )
    },
  ],
}

export const SlideInUp: Story = {
  decorators: [
    () => {
      const [key, setKey] = useState(0)
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <button
            className='btn btn-primary btn-sm'
            onClick={() => setKey((k) => k + 1)}
          >
            Replay
          </button>
          <motion.div
            key={key}
            variants={slideInUp}
            initial='hidden'
            animate='visible'
          >
            <DemoBox>slideInUp — inline content</DemoBox>
          </motion.div>
        </div>
      )
    },
  ],
}

export const StaggeredList: Story = {
  decorators: [
    () => {
      const [key, setKey] = useState(0)
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <button
            className='btn btn-primary btn-sm'
            onClick={() => setKey((k) => k + 1)}
          >
            Replay
          </button>
          <motion.div
            key={key}
            variants={staggerContainer(0.15)}
            initial='hidden'
            animate='visible'
            style={{ display: 'flex', flexDirection: 'column', gap: 8 }}
          >
            {[
              'Resolving hostname...',
              'Establishing TLS...',
              'Authenticating...',
              'Verifying schema...',
            ].map((text) => (
              <motion.div key={text} variants={staggerItem}>
                <DemoBox>{text}</DemoBox>
              </motion.div>
            ))}
          </motion.div>
        </div>
      )
    },
  ],
}

export const SpringBounce: Story = {
  decorators: [
    () => {
      const [key, setKey] = useState(0)
      return (
        <div
          style={{
            alignItems: 'flex-start',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          <button
            className='btn btn-primary btn-sm'
            onClick={() => setKey((k) => k + 1)}
          >
            Replay
          </button>
          <motion.div
            key={key}
            variants={springBounce}
            initial='hidden'
            animate='visible'
          >
            <DemoBox
              style={{
                background: 'var(--color-surface-success)',
                borderColor: 'var(--color-border-success)',
                color: 'var(--color-text-success)',
                fontWeight: 600,
              }}
            >
              ✓ Success
            </DemoBox>
          </motion.div>
        </div>
      )
    },
  ],
}

export const ShakeError: Story = {
  decorators: [
    () => {
      const [shaking, setShaking] = useState(false)
      return (
        <div
          style={{
            alignItems: 'flex-start',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          <button
            className='btn btn-danger btn-sm'
            onClick={() => {
              setShaking(false)
              requestAnimationFrame(() => setShaking(true))
            }}
          >
            Trigger shake
          </button>
          <motion.div variants={shakeX} animate={shaking ? 'shake' : 'idle'}>
            <DemoBox style={{ borderColor: 'var(--color-border-danger)' }}>
              Error: Invalid credentials
            </DemoBox>
          </motion.div>
        </div>
      )
    },
  ],
}

export const BadgeEntrance: Story = {
  decorators: [
    () => {
      const [key, setKey] = useState(0)
      return (
        <div
          style={{
            alignItems: 'flex-start',
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
          }}
        >
          <button
            className='btn btn-primary btn-sm'
            onClick={() => setKey((k) => k + 1)}
          >
            Replay
          </button>
          <motion.span
            key={key}
            variants={badgeEntrance}
            initial='hidden'
            animate='visible'
            style={{
              background: 'var(--color-surface-success)',
              borderRadius: 'var(--radius-full)',
              color: 'var(--color-text-success)',
              fontSize: 'var(--font-caption-xs-size)',
              fontWeight: 600,
              padding: '4px 12px',
            }}
          >
            Connected
          </motion.span>
        </div>
      )
    },
  ],
}

export const PageCrossfade: Story = {
  decorators: [
    () => {
      const [page, setPage] = useState(0)
      const pages = ['Page A', 'Page B', 'Page C']
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            {pages.map((label, i) => (
              <button
                key={label}
                className={`btn btn-sm ${
                  page === i ? 'btn-primary' : 'btn--outline'
                }`}
                onClick={() => setPage(i)}
              >
                {label}
              </button>
            ))}
          </div>
          <AnimatePresence mode='wait'>
            <motion.div
              key={page}
              variants={pageCrossfade}
              initial='hidden'
              animate='visible'
              exit='exit'
            >
              <DemoBox style={{ minHeight: 100 }}>
                {pages[page]} — crossfade transition
              </DemoBox>
            </motion.div>
          </AnimatePresence>
        </div>
      )
    },
  ],
}
