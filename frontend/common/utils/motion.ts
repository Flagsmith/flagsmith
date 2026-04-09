// =============================================================================
// Motion Presets — Reusable animation variants for the motion library
// Import these instead of defining raw values in components.
//
// Usage:
//   import { motion, AnimatePresence } from 'motion/react'
//   import { fadeIn, staggerContainer } from 'common/utils/motion'
//
//   <motion.div variants={fadeIn()} initial="hidden" animate="visible">
//     ...
//   </motion.div>
// =============================================================================

import type { Variants } from 'motion/react'

// -----------------------------------------------------------------------------
// Fade
// -----------------------------------------------------------------------------

/** Fade in with optional delay. Default 250ms. */
export const fadeIn = (delay = 0): Variants => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { delay, duration: 0.25, ease: [0.2, 0, 0.38, 0.9] },
  },
})

/** Fade out. Matches --easing-exit. */
export const fadeOut: Variants = {
  exit: {
    opacity: 0,
    transition: { duration: 0.2, ease: [0.2, 0, 1, 0.9] },
  },
  visible: { opacity: 1 },
}

// -----------------------------------------------------------------------------
// Slide
// -----------------------------------------------------------------------------

/** Slide in from right. 320ms, matches --easing-entrance. */
export const slideInRight: Variants = {
  exit: {
    opacity: 0,
    transition: { duration: 0.2, ease: [0.2, 0, 1, 0.9] },
    x: -40,
  },
  hidden: { opacity: 0, x: 40 },
  visible: {
    opacity: 1,
    transition: { duration: 0.32, ease: [0.0, 0, 0.38, 0.9] },
    x: 0,
  },
}

/** Slide in from below. Subtler, for inline content. */
export const slideInUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    transition: { duration: 0.25, ease: [0.0, 0, 0.38, 0.9] },
    y: 0,
  },
}

// -----------------------------------------------------------------------------
// Stagger
// -----------------------------------------------------------------------------

/** Container that staggers its children's entrance. */
export const staggerContainer = (staggerDelay = 0.1): Variants => ({
  hidden: {},
  visible: { transition: { staggerChildren: staggerDelay } },
})

/** Individual child item for use inside a stagger container. */
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3, ease: [0.0, 0, 0.38, 0.9] },
    y: 0,
  },
}

// -----------------------------------------------------------------------------
// Spring / Bounce
// -----------------------------------------------------------------------------

/** Spring bounce — success checkmarks, icons appearing. */
export const springBounce: Variants = {
  hidden: { opacity: 0, scale: 0 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { damping: 15, stiffness: 300, type: 'spring' },
  },
}

// -----------------------------------------------------------------------------
// Shake
// -----------------------------------------------------------------------------

/** Horizontal shake — error states, validation failures. */
export const shakeX: Variants = {
  idle: { x: 0 },
  shake: {
    transition: { duration: 0.4, ease: 'easeInOut' },
    x: [0, -8, 8, -4, 4, 0],
  },
}

// -----------------------------------------------------------------------------
// Badge / Chip
// -----------------------------------------------------------------------------

/** Badge slides down from above with fade. 250ms with 400ms delay. */
export const badgeEntrance: Variants = {
  hidden: { opacity: 0, y: -12 },
  visible: {
    opacity: 1,
    transition: { delay: 0.4, duration: 0.25, ease: [0.0, 0, 0.38, 0.9] },
    y: 0,
  },
}

// -----------------------------------------------------------------------------
// Page Transition (for AnimatePresence)
// -----------------------------------------------------------------------------

/** Crossfade between pages/states. Use with AnimatePresence mode="wait". */
export const pageCrossfade: Variants = {
  exit: {
    opacity: 0,
    transition: { duration: 0.15, ease: [0.2, 0, 1, 0.9] },
  },
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.25, ease: [0.2, 0, 0.38, 0.9] },
  },
}
