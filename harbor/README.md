# Harbor adapter

Runs Open ScholarPeer on the Paper-Reviewing-Exam benchmark as a first-class
Harbor agent.

`osp_harbor.agent:OpenScholarPeer` installs Node, OpenCode and a pinned OSP
release inside the task container, then runs one `osp review`. The released
controller does the work, so phase ordering, artifact validation, write
verification, checkpointing and the recommendation contract are all under test.
Nothing is mounted from the host and nothing is installed on it.

```bash
./run-osp.sh --install-only               # prove the install path, no model spend
./run-osp.sh de_novo_nanobody_discovery   # one task
./run-osp.sh                              # the six-task benchmark set
```

`EXAM_SHA`, `OSP_REF`, `MODEL`, `TIMEOUT_MULTIPLIER`, `JOBS_DIR` and `JOB_NAME`
override the defaults. Credentials are read from the environment (or the repo
`.env`) and never reach the command line, the job record, or the task.

## Agent kwargs

| `--ak` | Default | Meaning |
| --- | --- | --- |
| `osp_ref` | `main` | Git ref of OSP to install in the container |
| `osp_repository` | `a-green-hand-jack/open-scholar-peer` | Source repository |
| `opencode_version` | `1.18.25` | OpenCode version to install |
| `network_policy` | `scholarly` | `scholarly`, `online`, or `offline` |
| `qa_pairs` | `2` | Ordered Q&A pairs per criterion |
| `allow_lkm_spend` | `false` | Authorize billable Bohrium LKM calls |
| `variant` | unset | OpenCode model variant |
| `mode` | `autonomous` | `autonomous` or `collaborative` |
| `opencode_config` | unset | JSON provider config for endpoints OpenCode cannot infer |

## Reading a result

The Harbor reward only proves the submission contract: `review.md` exists and
is substantive. It is not a review-quality score and must not be read as one.
For development signal use the descriptive metrics instead — `mentions_location`
is 0 when a review never points at a section, equation or line — together with
`/logs/agent/osp-validate.json` and the phase attempt counts in the trail.

## The benchmark is not ours to change

Tasks and verifiers belong to `paper-review-bench`. This adapter adapts OSP to
the contract, never the contract to OSP.
