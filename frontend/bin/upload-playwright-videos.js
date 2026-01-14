#!/usr/bin/env node
/**
 * Upload Playwright test failure videos to Slack
 *
 * This script scans the Playwright test results directory for video files
 * and uploads them to the Slack #infra_tests channel.
 */

require('dotenv').config()
const fs = require('fs')
const path = require('path')
const uploadFile = require('./upload-file')

const REPORTS_DIR = path.join(__dirname, '..', 'reports', 'test-results')

async function uploadPlaywrightVideos() {
  if (!process.env.SLACK_TOKEN) {
    console.log('SLACK_TOKEN not set, skipping video upload')
    return
  }

  if (!fs.existsSync(REPORTS_DIR)) {
    console.log('No test results directory found, skipping video upload')
    return
  }

  // Find all video files recursively
  const videoFiles = []

  function findVideos(dir) {
    const files = fs.readdirSync(dir)
    for (const file of files) {
      const fullPath = path.join(dir, file)
      const stat = fs.statSync(fullPath)
      if (stat.isDirectory()) {
        findVideos(fullPath)
      } else if (file.endsWith('.webm') || file.endsWith('.mp4')) {
        videoFiles.push(fullPath)
      }
    }
  }

  findVideos(REPORTS_DIR)

  if (videoFiles.length === 0) {
    console.log('No video files found to upload')
    return
  }

  console.log(`Found ${videoFiles.length} video(s) to upload`)

  for (const videoFile of videoFiles) {
    try {
      console.log(`Uploading: ${videoFile}`)
      await uploadFile(videoFile)
      console.log(`Successfully uploaded: ${videoFile}`)
    } catch (error) {
      console.error(`Failed to upload ${videoFile}:`, error.message)
    }
  }
}

uploadPlaywrightVideos().catch(console.error)
