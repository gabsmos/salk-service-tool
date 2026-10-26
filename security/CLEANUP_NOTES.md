# Local secret cleanup

These replacements require protected runtime configuration before deployment. Variable names are listed in runtime-env.example; do not put values into this file or Git.

Run `python3 security/check_secrets.py` before committing, using a preinstalled Gitleaks. The checker reports type/path/line metadata only. It does not revoke credentials or clean existing history.

This overlay has not been applied to an existing checkout or published. Preserve unrelated edits. The audit apply helper checks HEAD, affected file blobs, staged changes and symlinks before allowing any write. It removes secret-file tracking without deleting runtime files.

Do not print an ordinary raw diff: removed lines may contain credentials. Review the redacted manifests and sanitized replacement source. Publishing/deployment, rotation/revocation, history rewrites and release rebuilds require the scoped approvals in the containment proposal.
