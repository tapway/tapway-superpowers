# Post-mortem: release tags drifted from the plugin manifests

**Date:** 2026-11-18
**Affected:** `tapway/tapway-superpowers` releases v2.8.0 – v2.8.3
**User impact:** `claude plugin update` kept resolving `2.7.2` while the release
page showed `v2.8.3`. Four releases were invisible to the marketplace resolver.

## Root cause

`release.yml` tags and publishes first, then writes the plain version into
`hermes/plugin/plugin.yaml`, `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`. That last step committed the bump and pushed
it straight to `master` — which requires a pull request — so GitHub rejected it:

```
remote: error: GH013: Repository rule violations found for refs/heads/master.
remote: - Cannot update this protected ref.
remote: - Changes must be made through a pull request.
 ! [remote rejected] HEAD -> master (push declined due to repository rule violations)
```

The step carried `continue-on-error: true` and swallowed the rejection as a
warning that also claimed, incorrectly, *"version files updated in the release
tag"*. The tag was created before the sync commit, so the tag contains the old
version too (`git show v2.8.3:hermes/plugin/plugin.yaml` → `2.7.2`).

A second, latent defect sat in the same step: the master stream computed its
base with `git tag -l "v*"`, which also matches `-stg` tags. A staging release
above the production tag would have made `PATCH` non-numeric
(`v1.1.0-stg` → cut -d. → `0-stg`).

## Why it wasn't caught

- `continue-on-error: true` on the sync step: the run stayed green.
- No workflow compares the tag with the manifests. The release page (tags) and
  the resolver (files) are read by different consumers, so nothing forced them
  to agree.
- The plugin manifests were also hand-bumped in PRs (2.7.0–2.7.2), giving the
  version two writers with no reconciliation.

## Prevention

- The sync opens a **PR** instead of pushing (`pull_requests: write`), and only
  the production stream writes manifests. `master` stays PR-only — no automation
  bypass was added.
- Version derivation extracted to `scripts/next_version.sh`, stream-filtered and
  covered by `tests/test_next_version.py` (8 cases, including "master ignores
  `-stg` tags").
- `scripts/check-release-drift.sh` compares the latest plain tag with all four
  manifest fields; `tests/test_release_drift.py` pins RED and GREEN; the
  `Release drift` workflow runs it daily.
- README: manifests are owned by the workflow; do not hand-bump in feature PRs.

## What the fix itself got wrong (and how it was caught)

- The first sync PR (#53) moved the two JSON manifests but not `hermes/plugin/plugin.yaml`;
  the drift detector reported it on its first real run.
- The second (#56) couldn't rename a CHANGELOG heading that did not exist, so the
  heading lagged; the detector caught that too.
- The PR-time guard `test_hermes_plugin.py` compared the manifests to the CHANGELOG
  heading, which cannot hold between a release and its sync PR — it went red on every
  PR in that window. It now compares the two manifests to each other; the tag-based
  drift check is the authority for the CHANGELOG.

Each of these was found by the check added in the same change, not by review.

## Regression tests

- `tests/test_next_version.py::test_master_stream_ignores_staging_tags`
- `tests/test_release_drift.py::test_red_when_the_tag_runs_ahead_of_the_manifests`
- `tests/test_release_drift.py::test_red_when_one_surface_disagrees`