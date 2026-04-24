"""Pure aggregation helpers for the data analyzer.

Kept free of database access so they can be unit-tested in isolation over a
list of plain JobRecord objects.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Iterable, Optional

# Tech skills extracted from job text. The tokenizer lowercases input before
# matching, so every entry here MUST be lowercase — "Python", "PYTHON", and
# "python" all hit the same canonical key.
KNOWN_SKILLS: frozenset[str] = frozenset(
    {
        # ------------------------- Programming languages -------------------------
        "python", "typescript", "javascript", "java", "kotlin", "scala", "go",
        "rust", "ruby", "php", "swift", "c#", "c++", "objective-c", "dart",
        "elixir", "erlang", "haskell", "clojure", "groovy", "perl", "lua",
        "julia", "matlab", "solidity", "bash", "shell", "powershell", "zsh",
        # --------------------- Front end: frameworks + libs ---------------------
        "react", "vue", "angular", "svelte", "next.js", "nuxt", "remix", "astro",
        "gatsby", "qwik", "preact", "ember", "jquery", "htmx", "stimulus",
        # --------------------- Front end: styling + tooling ---------------------
        "tailwind", "bootstrap", "bulma", "chakra", "mui", "sass", "scss",
        "webpack", "vite", "esbuild", "turbopack", "babel", "storybook",
        # ---------------- Front end: state / data / build helpers ----------------
        "redux", "mobx", "zustand", "recoil", "jotai", "apollo", "relay", "trpc",
        # --------------------------- Node / server JS ---------------------------
        "node", "deno", "bun", "express", "nestjs", "fastify", "koa", "hapi",
        "meteor", "strapi",
        # --------------------------- Python backend ---------------------------
        "django", "flask", "fastapi", "tornado", "starlette", "pyramid",
        "celery", "gunicorn", "uvicorn", "asyncio", "pydantic",
        # ------------------------- Other web backends -------------------------
        "spring", "rails", "laravel", "symfony", "phoenix", "gin", "actix",
        "axum", "hono", "asp.net", "dotnet", ".net",
        "graphql", "grpc", "websocket", "websockets", "microservices",
        # -------------------------------- Mobile -------------------------------
        "ios", "android", "xcode", "react-native", "flutter", "ionic", "expo",
        "swiftui", "jetpack", "cordova", "xamarin",
        # ------------------------- Data: databases / stores -------------------------
        "sql", "postgres", "postgresql", "mysql", "mariadb", "sqlite",
        "oracle", "mssql", "sqlserver", "mongodb", "redis", "memcached",
        "cassandra", "dynamodb", "cosmosdb", "elasticsearch", "opensearch",
        "neo4j", "influxdb", "timescale", "timescaledb", "clickhouse",
        "rocksdb", "etcd", "firebase", "firestore", "supabase", "planetscale",
        # ------------------------- Data: warehouses / lakes -------------------------
        "snowflake", "databricks", "bigquery", "redshift", "athena", "synapse",
        "glue", "emr", "dataflow", "dataproc", "delta", "iceberg", "hudi",
        # -------------------- Data: pipelines / stream processing --------------------
        "airflow", "prefect", "dagster", "luigi", "dbt", "spark", "kafka",
        "kinesis", "pulsar", "rabbitmq", "nats", "beam", "flink", "hadoop",
        "hive", "presto", "trino", "druid", "pinot",
        # ------------------------- Analytics / BI / viz -------------------------
        "tableau", "looker", "metabase", "superset", "qlik", "sigma",
        "powerbi", "quicksight",
        # -------------------------------- Cloud --------------------------------
        "aws", "gcp", "azure", "digitalocean", "linode", "heroku", "vercel",
        "netlify", "cloudflare", "fastly", "render", "railway", "fly", "fly.io",
        # -------------------------- Cloud-native infra --------------------------
        "kubernetes", "k8s", "docker", "podman", "containerd", "nomad",
        "consul", "vault", "rancher", "openshift", "istio", "linkerd", "envoy",
        "helm", "kustomize", "argocd", "flux",
        # -------------------------- IaC / config mgmt --------------------------
        "terraform", "pulumi", "cloudformation", "cdk", "ansible", "chef",
        "puppet", "salt", "packer",
        # ------------------------ Reverse proxies / web ------------------------
        "nginx", "apache", "caddy", "traefik", "haproxy",
        # --------------------------- DevOps / SRE ---------------------------
        "linux", "unix", "git", "github", "gitlab", "bitbucket", "jenkins",
        "circleci", "travis", "teamcity", "bamboo", "buildkite", "drone",
        "github-actions", "gitlab-ci", "azure-devops", "devops", "sre",
        # -------------------------- Observability / APM --------------------------
        "prometheus", "grafana", "datadog", "newrelic", "splunk", "elk",
        "logstash", "kibana", "fluentd", "fluentbit", "loki", "tempo", "jaeger",
        "zipkin", "opentelemetry", "otel", "sentry", "pagerduty", "opsgenie",
        # -------------------------- ML / AI: libraries --------------------------
        "pytorch", "tensorflow", "keras", "sklearn", "scikit-learn", "pandas",
        "numpy", "scipy", "matplotlib", "seaborn", "plotly", "bokeh", "dash",
        "streamlit", "gradio", "fastai", "opencv", "nltk", "spacy",
        # --------------------- ML / AI: models + frameworks ---------------------
        "llm", "gpt", "chatgpt", "claude", "gemini", "llama", "mistral",
        "bert", "transformer", "rnn", "cnn", "lstm", "yolo", "gan", "vae",
        # ----------------------- ML / AI: platforms / ops -----------------------
        "huggingface", "transformers", "diffusers", "langchain", "llamaindex",
        "pinecone", "weaviate", "qdrant", "chroma", "milvus", "faiss",
        "mlops", "mlflow", "kubeflow", "ray", "wandb", "sagemaker", "bedrock",
        "vertex", "openai", "anthropic", "cohere",
        # -------------------------- Data engineering --------------------------
        "etl", "elt", "cdc", "rag",
        # -------------------------------- Security --------------------------------
        "oauth", "oauth2", "saml", "jwt", "openid", "okta", "auth0", "kerberos",
        "ldap", "pki", "tls", "ssl", "iam", "rbac", "owasp", "csrf", "xss",
        "sqli", "burp", "metasploit", "nmap", "wireshark", "siem", "soar",
        "edr", "zero-trust",
        # --------------------------- Testing / QA ---------------------------
        "jest", "mocha", "jasmine", "vitest", "cypress", "playwright",
        "puppeteer", "selenium", "webdriver", "appium", "testcafe", "karma",
        "junit", "testng", "mockito", "rspec", "pytest", "unittest", "robot",
        "cucumber", "gherkin", "xctest", "espresso", "detox",
        # ------------------------- Design / product tools -------------------------
        "figma", "sketch", "invision", "zeplin", "adobe", "photoshop",
        "illustrator", "indesign", "xd", "blender", "miro", "lucidchart",
        # ---------------------- Game / 3D / graphics ----------------------
        "unity", "unreal", "godot", "threejs", "three.js", "babylon", "opengl",
        "webgl", "vulkan", "directx",
        # -------------------------- Process / PM tools --------------------------
        "agile", "scrum", "kanban", "jira", "confluence", "asana", "trello",
        "clickup",
        # -------------------------- Sales / marketing tools --------------------------
        "salesforce", "sfdc", "hubspot", "marketo", "pardot", "mailchimp",
        "sendgrid", "mixpanel", "amplitude", "pendo",
        "fullstory", "hotjar", "optimizely", "launchdarkly", "braze",
        "zendesk", "intercom", "freshdesk", "gainsight",
        # -------------------------- ERP / finance tools --------------------------
        "sap", "netsuite", "workday", "quickbooks", "oracle-erp",
        # -------------------------- Generic competencies --------------------------
        "ml", "ai", "nlp", "tdd", "bdd", "ddd", "saas", "paas", "iaas",
    }
)

# Tokens that frequently appear as multi-word phrases or with punctuation the
# single-token matcher can't handle. Map search substring -> canonical skill.
# Canonical keys do not have to appear in KNOWN_SKILLS.
PHRASE_ALIASES: dict[str, str] = {
    "next.js": "next.js", "nextjs": "next.js",
    "node.js": "node", "nodejs": "node",
    "vue.js": "vue", "vuejs": "vue",
    "three.js": "three.js", "threejs": "three.js",
    "react native": "react-native",
    "objective c": "objective-c", "objective-c": "objective-c",
    "machine learning": "ml",
    "deep learning": "ml",
    "artificial intelligence": "ai",
    "natural language processing": "nlp",
    "computer vision": "cv",
    "large language model": "llm", "large language models": "llm",
    "power bi": "powerbi",
    "microsoft excel": "excel",
    "google sheets": "sheets",
    "sql server": "sqlserver", "ms sql": "sqlserver",
    "active directory": "active-directory",
    "site reliability": "sre",
    "new relic": "newrelic",
    "spring boot": "spring",
    "ruby on rails": "rails",
    "asp.net": "asp.net", "asp net": "asp.net",
    ".net core": ".net", "dotnet core": ".net",
    "google cloud": "gcp", "google cloud platform": "gcp",
    "amazon web services": "aws",
    "microsoft azure": "azure",
    "ci/cd": "ci/cd", "ci / cd": "ci/cd", "continuous integration": "ci/cd",
    "continuous delivery": "ci/cd",
    "github actions": "github-actions",
    "gitlab ci": "gitlab-ci",
    "azure devops": "azure-devops",
    "test driven development": "tdd", "test-driven development": "tdd",
    "behavior driven development": "bdd", "behaviour driven development": "bdd",
    "domain driven design": "ddd",
    "object oriented": "oop",
    "infrastructure as code": "iac",
    "rest api": "rest",
    "single page application": "spa",
    "progressive web app": "pwa",
    "event driven": "event-driven",
    "zero trust": "zero-trust",
    "open ai": "openai",
    "hugging face": "huggingface",
}

TOKEN_RE = re.compile(r"[A-Za-z0-9+#.]+")
HTML_TAG_RE = re.compile(r"<[^>]+>")
HTML_ENTITY_RE = re.compile(r"&[a-z#0-9]+;", re.IGNORECASE)


def _strip_html(text: str) -> str:
    """Flatten HTML to plain text for keyword matching."""
    no_tags = HTML_TAG_RE.sub(" ", text)
    return HTML_ENTITY_RE.sub(" ", no_tags)


def tokenize_text(text: str) -> set[str]:
    """Return the set of known skills mentioned in ``text`` (case-insensitive).

    Accepts either plain strings or HTML; tags are stripped before matching.
    """
    if not text:
        return set()
    lowered = _strip_html(text).lower()
    matched: set[str] = set()

    for phrase, canonical in PHRASE_ALIASES.items():
        if phrase in lowered:
            matched.add(canonical)

    for raw in TOKEN_RE.findall(lowered):
        if raw in KNOWN_SKILLS:
            matched.add(raw)
    return matched


# Kept for backward compatibility with earlier call sites and tests.
tokenize_title = tokenize_text


def week_key(dt: datetime) -> str:
    """Return the ISO week key for ``dt`` in the form ``YYYY-Www`` (e.g. ``2026-W16``)."""
    year, week, _ = dt.isocalendar()
    return f"{year:04d}-W{week:02d}"


def aggregate_skills(
    jobs: Iterable, *, include_categories: bool = True
) -> dict[tuple[str, str, Optional[str]], int]:
    """Count skill mentions per (skill, week) and, if enabled, per (skill, week, category).

    Scans both ``title`` and ``description`` (HTML-stripped) on each job, so
    skills that only appear in the long-form posting still get picked up.
    """
    counter: Counter[tuple[str, str, Optional[str]]] = Counter()
    for job in jobs:
        title = getattr(job, "title", "") or ""
        description = getattr(job, "description", "") or ""
        skills = tokenize_text(f"{title}\n{description}")
        if not skills:
            continue
        week = week_key(getattr(job, "date_collected") or datetime.utcnow())
        category = getattr(job, "category", None)
        for skill in skills:
            counter[(skill, week, None)] += 1
            if include_categories and category:
                counter[(skill, week, category)] += 1
    return dict(counter)


def aggregate_companies(
    jobs: Iterable, *, include_categories: bool = True
) -> dict[tuple[str, str, Optional[str]], int]:
    """Count postings per (company, week) and, if enabled, per (company, week, category)."""
    counter: Counter[tuple[str, str, Optional[str]]] = Counter()
    for job in jobs:
        company = getattr(job, "company", None)
        if not company:
            continue
        week = week_key(getattr(job, "date_collected") or datetime.utcnow())
        category = getattr(job, "category", None)
        counter[(company, week, None)] += 1
        if include_categories and category:
            counter[(company, week, category)] += 1
    return dict(counter)
