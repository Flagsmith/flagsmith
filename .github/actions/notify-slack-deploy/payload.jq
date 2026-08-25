# Slack Block Kit payload for a deploy notification.
# Run with jq -n and the --arg values listed in action.yml.

($environment | (.[0:1] | ascii_upcase) + .[1:]) as $env_name |

# Only success and cancelled need their own words. Everything else GitHub
# reports, timed_out and skipped included, means the deploy did not happen.
(if $conclusion == "success" then
  {
    headline: "🚀 \($service) deployed to \($environment)",
    body: "🧪 *\($env_name) smoke test required*\n\nPlease verify the application directly in \($environment).",
    actor_label: "Deployed by",
    link_app: true
  }
elif $conclusion == "cancelled" then
  {
    headline: "⏭️ \($service) deploy to \($environment) stopped",
    # run-tests cancels itself in progress when the next commit lands on main,
    # which is upstream of the deploy. A hand cancellation can land anywhere,
    # including mid-deploy, so do not assert what the environment is serving.
    body: "Cancelled before finishing. If a newer commit superseded this run, \($environment) is unchanged and the newer run deploys instead. If it was cancelled by hand, check the run to see whether the deploy had started.",
    actor_label: "Pushed by",
    link_app: false
  }
else
  {
    headline: "🛑 \($service) deploy to \($environment) failed",
    body: "\($env_name) is unchanged and still serving the previous release.",
    actor_label: "Pushed by",
    link_app: false
  }
end) as $copy |

{
  # Slack honours username on this webhook but ignores icon_emoji. The avatar
  # comes from the icon set on the Slack app itself.
  username: "\($service) Deploy",
  text: $copy.headline,
  blocks: [
    {
      type: "header",
      text: { type: "plain_text", text: $copy.headline }
    },
    {
      type: "section",
      text: { type: "mrkdwn", text: $copy.body }
    },
    {
      type: "section",
      fields: (
        [
          { type: "mrkdwn", text: "*Commit:*\n\($short_sha)" },
          { type: "mrkdwn", text: "*\($copy.actor_label):*\n@\($actor)" }
        ]
        # Slack renders this date token in the reader's own timezone; the text
        # after the pipe is the fallback everywhere else.
        + (if $started_epoch != "" then
            [{ type: "mrkdwn", text: "*Started:*\n<!date^\($started_epoch)^{time}|\($started_label)>" }]
           else [] end)
        + (if $duration != "" then
            [{ type: "mrkdwn", text: "*Duration:*\n\($duration)" }]
           else [] end)
      )
    },
    {
      type: "actions",
      elements: (
        (if $copy.link_app then
          [{
            type: "button",
            text: { type: "plain_text", text: "Open \($env_name)" },
            url: $app_url
          }]
         else [] end)
        + [{
            type: "button",
            text: { type: "plain_text", text: "View GitHub Actions" },
            url: $run_url
          }]
      )
    }
  ]
}
