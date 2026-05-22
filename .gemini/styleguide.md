### PR009: Submit all comments as a single batch review

Use GitHub's "Start a review" → "Submit review" workflow. Avoid posting individual comments one at a time.

> *One notification with full context beats a drip-feed of pings. The author sees the complete picture and can plan their work.*

### PR010: Label comments by intent

Some review comments don’t have to be addressed.

Be sure to clearly communicate this to the PR author, for example, by using a “suggestion:” or “nitpick:” prefix. There’s a more detailed [Conventional Comments](https://conventionalcomments.org/) framework that you can follow to label your intent more specifically.

> *Unlabelled comments create ambiguity — is this a must-fix or a nice-to-have? Labels eliminate guesswork and prevent unnecessary round-trips.*

### PR011: Use neutral, non-accusatory language

Say "This function doesn't close the connection" instead of "You forgot to close the connection." Ask questions instead of giving commands: "What do you think about extracting this?" rather than "Extract this." Avoid "just," "simply," "obviously."

> *Written feedback lacks tone. Neutral language prevents misinterpretation and keeps reviews collaborative.*

### PR012: Approve when the PR improves code health, not when it's perfect

If the PR makes the codebase better and passes all checks, approve it. There is no such thing as perfect code, only better code. Don't block for polish.

> *Blocking on perfection creates frustration and slows delivery without proportional quality gains.* 

### PR013: Use "Request Changes" without hesitation

If a PR has issues that must be addressed before merging, submit the review as **Request Changes** — not as a Comment with suggestions. This is not a personal judgement; it is a clear signal that the PR is not ready yet. Use it as many times as necessary until the PR actually looks good to merge. Approving out of politeness helps no one.

> *A "Comment" review with blocking feedback is ambiguous — the author may interpret it as optional. "Request Changes" removes all doubt and keeps the review loop honest. Candour is a kindness; silent approvals are not.*
