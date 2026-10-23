# Usage dashboard fixtures

Daily API call counts for the usage dashboard stories.

Each file is one scenario: an array of days, each with the four billable
request types. Hand editable, so a spike, a plateau or a quiet weekend can be
drawn deliberately rather than generated.

`toUsageResponse` in `../usage.ts` expands them into the shape the API returns.
