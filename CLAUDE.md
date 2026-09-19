# Notes for Claude Code sessions

The specification for triage work is `.github/copilot-instructions.md`. Read it
first, in full. This file only records what a Claude Code cloud session needs
to know about its own environment, learned the hard way.

## Network: "Host not in allowlist" is the session, not the source

Cloud sessions run behind an egress proxy that enforces the environment's
network access level. Under the default **Trusted** level only package
registries and GitHub are reachable. Every other host is refused by the proxy
before the request leaves the sandbox. It looks like this:

```
curl: (56) CONNECT tunnel failed, response 403
Host not in allowlist: web.archive.org. Add this host to your network egress settings to allow access.
```

Read that correctly:

- It is **not** archive.org rate-limiting you, and it is not the source site
  being down or unreachable. Do not write "the archive lookup failed" or "the
  page could not be fetched" in a PR body, a source `note` or a reply.
- It is **not** something to retry or route around. Report the host, say it is
  the environment allowlist, and ask for it to be added.
- Web search and MCP connectors still work at this level because their traffic
  goes through Anthropic's servers, not the session's network. That is why
  `microsoft_docs_fetch` can read learn.microsoft.com while `curl` cannot.
  Use them to confirm dates and stages, but they do not replace reading the
  primary page or recording an `archived_url`.

The fix is on the environment, not in the session: open the environment,
set **Network access** to **Custom**, tick **Also include default list of
common package managers**, and list the hosts below one per line in
**Allowed domains**. Documentation:
<https://code.claude.com/docs/en/cloud-environments#allow-specific-domains>.

Hosts this dataset cites, all confirmed refused on 2026-09-19 under the
default level unless marked:

```
web.archive.org
archive.org
github.blog
docs.github.com
techcommunity.microsoft.com
learn.microsoft.com
microsoft.ai
www.microsoft.com          (reachable at the default level)
openai.com
community.openai.com
deploymentsafety.openai.com
www.anthropic.com
blog.google
ai.google.dev
x.ai
huggingface.co
mistral.ai
docs.mistral.ai
api-docs.deepseek.com
qwen.ai
```

Check reachability in one pass before starting a batch, and add any new
publisher a candidate cites to the list above when you find it refused:

```bash
for h in web.archive.org github.blog techcommunity.microsoft.com openai.com; do
  printf '%-32s ' "$h"; curl -sS -m 15 "http://$h/" -o /dev/null -w '%{http_code}\n'
done
```

A `403` with the "Host not in allowlist" body is the allowlist. Anything else is
the site.

## Snapshots: the CDX API is the lookup, and it doubles as the reader

`.github/copilot-instructions.md` step 5 already says to use the read-only
CDX API and to avoid the availability API. Two additions:

1. When a source host is refused but `web.archive.org` is allowed, the archive
   is how you read the page as well as how you cite it. Look up the capture,
   then fetch the raw original with the `id_` flag:

   ```
   https://web.archive.org/cdx/search/cdx?url=<url-without-scheme>&filter=statuscode:200&limit=5
   https://web.archive.org/web/<timestamp>id_/<original>
   ```

   That gives the verbatim quote, the page's own dateline and the
   `archived_url` in one step, with no failed-fetch disclosure needed.

2. If `web.archive.org` itself is refused, that is the allowlist case above.
   Stop and report it. Do not fall back to quoting the candidate issue's
   excerpt as if it were the page; the guide already says an issue excerpt is
   not the page.

## Candidate issues

`bibble-envoy[bot]` files candidates from news feeds. The **Flagged** timestamp
is when the feed surfaced the item, which can be months after publication:
the Copilot Studio Mistral Medium 3.5 post carries a 28 May 2026 dateline and
was flagged on 19 September 2026. Always read the page's own date.
