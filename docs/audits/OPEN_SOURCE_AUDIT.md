# Open Source Audit

## Present

- MIT license.
- README with local/Docker quick starts.
- Contribution and architecture rules.
- Code of conduct and private security-reporting guidance.
- Changelog, roadmap, release notes, checklist, status, and migration guide.
- Deterministic package script and checksum.
- Git ignore rules for secrets/builds/caches.
- SHA-pinned CI actions and Dependabot configuration.
- Examples for development and production environment variables.
- Generated OpenAPI contract.

## Repository hygiene

No old repository ZIP, attached-assets folder, generated React/Express builds,
source maps, egg metadata, node modules, virtual environment, database, or cache
is included in the release package. Historical migration revision names remain
because changing applied Alembic IDs would be unsafe.

## Remaining improvements

- Add issue and pull-request templates after the official GitHub namespace and
  maintainer workflow are chosen.
- Add signed provenance/SBOM after container/release CI is verified.
- Add exact maintainer contact/security advisory link once the public repository
  exists.

**Open source readiness:** 96% (24 of 25 rubric items complete; release evidence
and repository-host-specific templates are the outstanding item).
