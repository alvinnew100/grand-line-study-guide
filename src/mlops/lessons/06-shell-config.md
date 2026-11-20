# Linux shell essentials and configuration management

## Why shell skills matter for MLOps

Every container, CI runner, training VM and Kubernetes pod you will touch runs Linux. When a training job
dies at 3 a.m., you will be `ssh`-ing into a node or `kubectl exec`-ing into a pod, reading logs,
checking disk and GPU memory, and inspecting environment variables. This lesson is the survival kit,
followed by the second half of the "how does the code know what to do" story: **configuration
management**.

## Navigating and inspecting

```bash
pwd; ls -lah; cd /data/projects
tree -L 2                       # directory overview (if installed)
du -sh * | sort -h              # what is eating disk?
df -h                           # free space per filesystem (full disks kill training jobs)
find . -name "*.parquet" -size +100M -mtime -7    # large parquet files changed in last 7 days
head -n 5 data.csv; tail -f train.log             # follow a log as it grows
wc -l data.csv                  # count lines (rows + header)
less +F app.log                 # scrollable follow mode
```

## Text processing pipelines

The Unix philosophy — small tools that do one thing and compose through pipes — is the ancestor of every
data pipeline. Kleppmann (*DDIA*, ch. 10) opens his chapter on batch processing with exactly this: a
chain like `cat | awk | sort | uniq -c | sort -r | head` analysing a web log is a tiny batch job, and
MapReduce generalises the same idea across machines.

```bash
# top 5 endpoints by request count from an access log
awk '{print $7}' access.log | sort | uniq -c | sort -rn | head -5

# count prediction errors by model version in JSON logs
grep '"level":"error"' service.log | jq -r '.model_version' | sort | uniq -c

# p95-ish latency from a column of numbers (nearest rank)
cut -d, -f3 latencies.csv | sort -n | awk '{a[NR]=$1} END {print a[int(NR*0.95+0.999)]}'

# replace a config value in place
sed -i 's/batch_size: 32/batch_size: 64/' configs/train.yaml
```

| Tool | Use |
|---|---|
| `grep -rn "pattern" src/` | search text |
| `cut`, `awk` | select / compute columns |
| `sort`, `uniq -c` | group and count |
| `sed` | stream edit |
| `jq` | query and transform JSON (structured logs, API responses) |
| `xargs`, `parallel` | run a command per input line, optionally in parallel |
| `tee` | write to file and stdout simultaneously |

### Redirection and exit codes

```bash
python train.py > train.log 2>&1      # stdout and stderr to file
python train.py 2>&1 | tee train.log  # and see it live
python train.py && echo "ok" || echo "failed with $?"
```

Every process returns an **exit code**: 0 for success, non-zero for failure. CI systems, orchestrators and
Kubernetes all decide "did the step pass?" from the exit code — so your training script must
`sys.exit(1)` (or raise) on failure, never print an error and exit 0.

## Processes, resources and GPUs

```bash
ps aux | grep train             # running processes
top / htop                      # live CPU and memory
free -h                         # RAM
nvidia-smi                      # GPU utilisation, memory, processes
watch -n 1 nvidia-smi           # refresh every second
kill <pid>; kill -9 <pid>       # SIGTERM (graceful) vs SIGKILL (immediate)
nohup python train.py > log 2>&1 &     # survive logout
tmux new -s train               # persistent terminal session; detach with Ctrl-b d
```

> [!NOTE]
> Kubernetes stops a pod by sending **SIGTERM**, waiting for `terminationGracePeriodSeconds` (30 s by
> default), then sending SIGKILL. A serving process should handle SIGTERM by finishing in-flight requests;
> a training job should checkpoint. Uvicorn and Gunicorn handle SIGTERM gracefully out of the box.

## Permissions, users and networking basics

```bash
chmod +x scripts/run.sh         # make executable
chmod 600 ~/.ssh/id_ed25519     # private keys must be private
chown app:app /models -R
whoami; id                      # containers should not run as root (lesson 17)
curl -s localhost:8000/health   # hit a local endpoint
curl -X POST localhost:8000/predict -H 'Content-Type: application/json' -d '{"tenure": 12}'
ss -tlnp                        # which ports are listening
ssh -L 5000:localhost:5000 user@trainbox   # tunnel a remote MLflow UI to your laptop
scp model.onnx user@host:/models/
```

## Shell scripts that do not lie

```bash
#!/usr/bin/env bash
set -euo pipefail        # exit on error, on unset variables, and on failures inside pipes
IFS=$'\n\t'

DATA_DIR="${DATA_DIR:-/data}"     # default if unset
MODEL_URI="${1:?usage: score.sh MODEL_URI}"   # required argument

echo "[$(date -Is)] scoring with ${MODEL_URI}"
python -m churn.score --model "${MODEL_URI}" --input "${DATA_DIR}/today.parquet"
```

`set -euo pipefail` is the single most valuable line in any shell script: without it, a failing step in
the middle is silently ignored and the script "succeeds".

## Environment variables

Environment variables are the universal configuration interface between platforms and processes:
Docker (`-e`, `env_file`), Kubernetes (`env`, `envFrom` ConfigMaps/Secrets), CI (`env:`), and cloud
services all inject config this way.

```bash
export MLFLOW_TRACKING_URI=http://mlflow:5000
env | grep MLFLOW
MODEL_STAGE=prod python serve.py     # set for one command only
```

## Configuration management

### The twelve-factor rule

The *Twelve-Factor App* methodology says: **store config in the environment**, strictly separated from
code. Config is everything that varies between deploys (dev, staging, prod): URLs, credentials, feature
flags, resource sizes. The litmus test: could you open-source the code right now without leaking
credentials?

ML adds a second kind of configuration: **experiment configuration** — hyperparameters, feature lists,
data windows, model type. This varies between *runs*, and must be versioned and logged with each run.

| Kind | Examples | Where it lives |
|---|---|---|
| Deployment config | DB URL, MLflow URI, log level, replicas | env vars, ConfigMaps, secret manager |
| Secrets | API keys, passwords | secret manager / K8s Secrets, never Git |
| Experiment config | learning rate, features, date window | YAML in Git + logged to the tracker |
| Runtime flags | rollout percentage, kill switch | feature-flag service or config store |

### Typed settings with pydantic-settings

Read deployment config from environment variables with validation and defaults. Errors fail fast at
startup instead of at the first request.

```python
# src/churn/serve/settings.py
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHURN_", env_file=".env")

    model_uri: str = "models:/churn@champion"
    mlflow_tracking_uri: HttpUrl = "http://localhost:5000"
    log_level: str = "INFO"
    max_batch_size: int = Field(32, ge=1, le=1024)
    request_timeout_s: float = 2.0

settings = Settings()   # reads CHURN_MODEL_URI, CHURN_MAX_BATCH_SIZE, ... ; raises if invalid
```

### Hierarchical experiment config with Hydra / OmegaConf

Hydra composes configs from groups and lets you override any value from the command line — and records
the final, resolved config for every run in its output directory.

```yaml
# configs/train.yaml
defaults:
  - model: gbm           # picks configs/model/gbm.yaml
  - data: last_90_days
  - _self_
seed: 42
target: churned_30d
features: [tenure_months, plan, monthly_charges, support_tickets_30d]
```

```yaml
# configs/model/gbm.yaml
name: hist_gradient_boosting
params:
  learning_rate: 0.05
  max_iter: 400
  max_leaf_nodes: 31
```

```bash
python -m churn.train model=logreg seed=7 model.params.C=0.5
python -m churn.train --multirun model.params.learning_rate=0.01,0.05,0.1   # simple sweep
```

### A minimal config loader you can run

Here is the core mechanism of layered configuration — defaults, then a file, then environment variables,
then CLI overrides, with later layers winning — implemented with plain dicts:

```python-run
import copy, json

def deep_merge(base, override):
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def set_dotted(cfg, dotted, value):
    keys = dotted.split(".")
    d = cfg
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = json.loads(value) if value[:1] in "0123456789[{-tfn" else value

defaults = {"seed": 0, "model": {"name": "gbm", "params": {"learning_rate": 0.1, "max_iter": 100}}}
file_cfg = {"seed": 42, "model": {"params": {"max_iter": 400}}}
env = {"TRAIN__MODEL__PARAMS__LEARNING_RATE": "0.05"}   # pretend environment
cli = ["model.params.max_iter=800", "model.name=gbm_v2"]

cfg = deep_merge(defaults, file_cfg)
for k, v in env.items():
    if k.startswith("TRAIN__"):
        set_dotted(cfg, ".".join(p.lower() for p in k[7:].split("__")), v)
for item in cli:
    key, val = item.split("=", 1)
    set_dotted(cfg, key, val)
print(json.dumps(cfg, indent=2))
```

> [!TIP]
> Whatever the mechanism, **log the fully resolved config** with every run (MLflow `log_dict` or
> `log_params`) and bake the serving config's hash into your logs. "Which config produced this model?"
> must always have an answer.

### Config anti-patterns

- Hard-coded paths and URLs in code (`/home/alice/data`).
- Secrets in YAML committed to Git.
- Untyped configs where `"0.1"` (string) silently becomes a learning rate.
- Copies of the same config per environment that drift (`train_prod.yaml`, `train_prod_final2.yaml`).
  Prefer a base plus small overrides.
- Config changes deployed without review: treat config diffs like code diffs (Sculley et al. call
  configuration debt out explicitly).

> [!INTERVIEW]
> "Where do you put the learning rate, the database password and the canary percentage?" —
> Learning rate: versioned experiment config (YAML in Git, logged per run). Password: secret manager,
> injected as env var/K8s Secret. Canary percentage: deployment/rollout config or a feature-flag system,
> changeable without rebuilding the image.

## Summary

- Know your way around files, logs, processes, GPUs, ports and permissions; pipes and `jq` make you fast.
- Exit codes are the contract with CI and orchestrators; use `set -euo pipefail` in scripts.
- Handle SIGTERM gracefully in services and training jobs.
- Separate deployment config (env vars, twelve-factor), secrets (secret manager) and experiment config
  (versioned YAML, logged per run). Validate config with types and fail fast.

```quiz
[
  {"q": "What does `set -euo pipefail` do in a bash script?",
   "options": ["Enables GPU usage", "Exits on errors, on unset variables, and when any command in a pipe fails", "Runs the script in parallel", "Suppresses all output"],
   "answer": 1, "explain": "Without it, failing commands in the middle of a script are silently ignored."},
  {"q": "A CI step runs `python train.py`, which prints 'ERROR: data missing' and exits with code 0. What happens?",
   "options": ["CI marks the step failed", "CI marks the step as passed, hiding the failure", "CI retries automatically", "Kubernetes restarts it"],
   "answer": 1, "explain": "CI and orchestrators judge success by exit code; scripts must exit non-zero on failure."},
  {"q": "Which signal does Kubernetes send first when stopping a pod?",
   "options": ["SIGKILL", "SIGTERM", "SIGHUP", "SIGSTOP"],
   "answer": 1, "explain": "SIGTERM first, then SIGKILL after the grace period."},
  {"q": "According to the twelve-factor methodology, where should deployment config live?",
   "options": ["Hard-coded constants", "In environment variables, separate from code", "In the Docker image name", "In comments"],
   "answer": 1, "explain": "Config that varies between deploys belongs in the environment."},
  {"q": "Where should hyperparameters for a training run be stored?",
   "options": ["Only in the engineer's memory", "In versioned config files and logged with each run", "In a Kubernetes Secret", "In the model filename only"],
   "answer": 1, "explain": "Experiment config must be versioned and recorded for reproducibility."},
  {"q": "What does `jq -r '.model_version'` do when applied to JSON log lines?",
   "options": ["Deletes the field", "Extracts the model_version field as raw text from each JSON object", "Validates JSON schema", "Compresses logs"],
   "answer": 1, "explain": "jq queries JSON; -r prints raw strings without quotes."},
  {"q": "What is the advantage of pydantic-settings for service configuration?",
   "options": ["It trains models", "It validates and types environment-based config, failing fast at startup", "It replaces Docker", "It encrypts logs"],
   "answer": 1, "explain": "Invalid config (e.g., a negative batch size) raises at startup rather than at the first request."}
]
```

> **Source:** Martin Kleppmann, *Designing Data-Intensive Applications*, ch. 10 (Batch processing with Unix tools); The Twelve-Factor App (12factor.net), factor III *Config*; Hydra and pydantic-settings documentation; Kubernetes documentation, *Pod lifecycle — termination of pods*; Sculley et al. (2015) on configuration debt.
