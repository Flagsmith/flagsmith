if (!process.env.SLACK_TOKEN) {
  return
}

const SLACK_TOKEN = process.env.SLACK_TOKEN

async function toChannel(message, channel) {
  // eslint-disable-next-line
  console.log(`sending to channel: ${channel} message: ${message}`)
  try {
    const res = await fetch('https://slack.com/api/chat.postMessage', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        Authorization: `Bearer ${SLACK_TOKEN}`,
      },
      body: JSON.stringify({ channel: `#${channel}`, text: message }),
    })
    const data = await res.json()
    if (!data.ok) throw new Error(data.error)
  } catch (error) {
    // eslint-disable-next-line
    console.log(`Error posting to Slack:${error}`)
  }
}

module.exports = toChannel
