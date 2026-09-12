# Publish AgentStreamDeck to PyPI

**Published:** [agentstreamdeck 2.1.1](https://pypi.org/project/agentstreamdeck/2.1.1/)
on 2026-09-12 using trusted publishing. The steps below document setup and future releases.

The repository is prepared for keyless publishing. Account-side PyPI authorization
must be configured by someone with access to the PyPI account. The previous `agentdeck` name was rejected by PyPI as too similar to an existing
project. The new distribution name is `agentstreamdeck`; PyPI must still accept
the pending publisher. Rename the GitHub repository before configuring it.

## Exact first-time setup

1. Sign in to [PyPI](https://pypi.org/account/login/), verify your email and complete
   the account's required two-factor authentication setup.
2. Open [PyPI account Publishing](https://pypi.org/manage/account/publishing/).
   In **Add a new pending publisher**, choose **GitHub** and enter:

   | Field | Exact value |
   |---|---|
   | PyPI project name | `agentstreamdeck` |
   | Owner | `darkmatter2222` |
   | Repository name | `AgentStreamDeck` |
   | Workflow name | `pypi.yml` |
   | Environment name | `pypi` |

   Use the filename `pypi.yml`, not `.github/workflows/pypi.yml` and not the visible
   workflow title. Click **Add**. A pending publisher creates the project on the
   first successful upload; it does not reserve the name before then.
3. Open [GitHub repository Environments](https://github.com/darkmatter2222/AgentStreamDeck/settings/environments).
   Create an environment named **pypi** if it does not already exist. Under its
   deployment branch/tag rules choose selected branches/tags and add branch
   **main**. Save the rule. Any existing environment review requirements continue
   to apply. No `PYPI_API_TOKEN` or password secret is needed.
4. Open [Signed Python release](https://github.com/darkmatter2222/AgentStreamDeck/actions/workflows/pypi.yml),
   choose **Run workflow**, select **main**, and click **Run workflow**. Approve the
   environment deployment if your configured environment requires it.
5. Wait for both **build** and **publish** to finish successfully. The workflow
   builds the package, SBOM and checksums, records provenance and uploads the
   wheel/sdist using short-lived OIDC credentials with PyPI attestations.
6. Verify [the project on PyPI](https://pypi.org/project/agentstreamdeck/2.1.1/), then install:

   ```powershell
   python -m pip install --upgrade agentstreamdeck==2.1.1
   ocdeck --version
   ```

This installs the Python command/runtime assets. It does not automatically create
the OpenCode scheduled task, grant native hook trust, or install hooks in projects;
follow the README for those steps.

## If the project already exists

If **you own** `agentstreamdeck`, use that project's **Manage → Publishing** page and
add a GitHub publisher with the same owner/repository/workflow/environment values.
If somebody else owns it or PyPI rejects the name, choose an available distribution
name, change `[project].name` in `pyproject.toml`, update the documentation/install
commands, and configure the pending publisher for that exact name. The `ocdeck`
CLI/module name can remain unchanged. Do not upload to someone else's project.

## Troubleshooting

- **Invalid publisher / token exchange rejected:** compare all five values exactly;
  the workflow must run from `main` in `darkmatter2222/AgentStreamDeck`, in environment `pypi`.
- **Publish job skipped:** the workflow was dispatched from a different branch/repository.
- **Waiting for approval:** approve the `pypi` environment deployment in the run UI.
- **File already exists:** PyPI never replaces an uploaded distribution. Inspect the
  existing release before retrying; use a new version for changed package contents.
- **Name unavailable:** a pending publisher does not reserve a project name.

Official references: [new-project trusted publishing](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
and [adding a publisher to an existing project](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

The initial v2.1.1 merge also starts this workflow automatically. Check that run
before dispatching manually to avoid uploading the same version twice.
