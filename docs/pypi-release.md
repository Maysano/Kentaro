# PyPI release automation

Kentaro publishes through GitHub Actions and [PyPI Trusted
Publishing](https://docs.pypi.org/trusted-publishers/). The workflow never uses a
stored PyPI API token or a repository secret.

## One-time PyPI setup

An owner of the `kentaro` project on PyPI must register this GitHub Trusted Publisher:

| Setting | Value |
| --- | --- |
| Owner | `Maysano` |
| Repository | `Kentaro` |
| Workflow file | `publish-pypi.yml` |
| Environment | `pypi` |

For the first release, create a pending publisher with the same values before the
project exists on PyPI. In GitHub, configure the `pypi` environment with the required
release protection rules and only the maintainers who may publish releases. Do not add
a `PYPI_API_TOKEN` secret.

## What the workflows do

`ci.yml` runs on pull requests and changes to `main`. It tests Python 3.11 and 3.12,
builds the source and wheel distributions, validates package metadata with `twine`, and
retains the distributions as short-lived workflow artifacts.

`publish-pypi.yml` runs only when a GitHub Release is published. It checks out the
release tag, requires the tag to exactly match `v<version>` from `pyproject.toml`, runs
the complete test suite, builds and validates distributions, then requests a short-lived
OIDC identity to publish through PyPI Trusted Publishing. Publishing is held behind the
GitHub `pypi` environment.

## Release procedure

1. Update `pyproject.toml`, [release notes](../RELEASE_NOTES.md), and any documentation
   required by the version change.
2. Merge the release commit to `main` after CI passes.
3. Create a GitHub Release tagged exactly `v<version>` at that release commit, initially
   as a draft if review is needed.
4. Verify its notes and target commit, then publish the GitHub Release.
5. Approve the protected `pypi` environment when GitHub requests it. The publish job
   then uploads the source distribution and wheel.
6. Verify the PyPI project page and install the exact published version in a clean
   environment.

PyPI versions are immutable. If publishing fails after a version is publicly uploaded,
make a corrective release with a new version rather than attempting to overwrite it.
