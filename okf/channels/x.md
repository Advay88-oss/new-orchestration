---
type: Channel
title: X (Twitter)
description: The publishing target. Single post with one rendered card.
tags:
- channel
- publishing
status: stable
platform_id: x
max_chars: 280
publisher: opencli twitter post
account: '@AnandAdvay91289'
---

# X (Twitter)

Published through OpenCLI's Chrome bridge, which drives a logged-in browser
profile rather than an API.

**The account is a personal handle, not a brand handle.** For a company other
than the operator's own, per-tenant account ownership is an open question with
legal as well as technical parts — settle it before the first publish.

**Failure modes:** a 60s `TIMEOUT`, and `No SW` when the daemon is alive but no
extension service worker is attached, which breaks reads as well as writes. A
timeout is not proof the post failed — read the timeline before retrying or you
will double-post.
