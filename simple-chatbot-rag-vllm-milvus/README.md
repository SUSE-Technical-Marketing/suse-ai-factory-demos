# Simple Chatbot with RAG (vLLM + Milvus) — Install & Configuration Guide

> **Simple Chatbot with RAG** using `vllm`, `open-webui`, `milvus`, and `open-webui-mcpo`.
> A **GPU‑accelerated** blueprint: vLLM serves the model over an OpenAI‑compatible API, and
> retrieval‑augmented generation uses a standalone **Milvus** vector database.

The production‑leaning sibling of the CPU/ollama *Simple Chatbot with RAG* blueprint — same demo story
(private LLM chat, grounded RAG answers, MCP tool calling), but with **vLLM** for fast GPU inference and
**Milvus** as a real external vector store instead of embedded ChromaDB. You deploy the blueprint, then adjust
a handful of values for your environment.

> **In a hurry?** [QUICKSTART.md](./QUICKSTART.md) is the condensed, K8s‑expert version — the same value
> changes and gotchas, no walkthrough.

---

## What you can demo

| Capability | What the audience sees |
|---|---|
| **Private GPU‑served LLM chat** | A ChatGPT‑style UI answering from a locally‑served model (`Phi-3-mini-4k-instruct`) via vLLM, no external API. |
| **RAG (grounded answers)** | Upload your own documents; the bot answers questions from them **with citations**, and visibly *doesn't* know the same facts without the docs. Embeddings are stored in **Milvus**. |
| **MCPO tool calling** | The bot uses a real **MCP tool** (a persistent knowledge‑graph "memory") through the open‑webui‑mcpo OpenAPI proxy — "remember this" / "what do you know about me?". |

---

## Architecture

The blueprint deploys four apps into one namespace (`simple-chatbot-with-rag-vllm-and-milvus-system`):

| App | Role |
|---|---|
| `vllm` | Serves the LLM (`microsoft/Phi-3-mini-4k-instruct`) over an OpenAI‑compatible API. A **router** (`vllm-router-service:80`, `/v1`) fronts one or more **serving engines**. **Requires a GPU.** |
| `open-webui` | Chat UI + RAG. Talks to vLLM via the OpenAI API and to Milvus for the vector store. Exposed via Ingress. |
| `milvus` | Vector database in **standalone** mode (milvus + etcd + MinIO) at `milvus:19530`. |
| `open-webui-mcpo` | MCP‑to‑OpenAPI proxy exposing MCP tools (the `memory` server) at `open-webui-mcpo:8000`. |

**Wiring that ships correct in the defaults — don't change these:**
- `open-webui` → vLLM: `OPENAI_API_BASE_URL: http://vllm-router-service/v1`, `OPENAI_API_KEY: dummy`, `ENABLE_OPENAI_API: "true"`.
- `open-webui` → Milvus: `VECTOR_DB: milvus`, `MILVUS_URI: http://milvus:19530`.

---

## Prerequisites

- **SUSE AI Factory** installed and configured.
- **NVIDIA GPU (required).** vLLM will not run on CPU. You need the **GPU Operator / device plugin** so the node
  advertises `nvidia.com/gpu`, and the `nvidia` runtime class:
  ```bash
  kubectl get nodes -o jsonpath='{.items[*].status.capacity.nvidia\.com/gpu}{"\n"}'   # non-empty
  kubectl get runtimeclass nvidia                                                       # exists
  ```
  The default model (`Phi-3-mini-4k-instruct`) requests **1 GPU / 6 CPU / 16 GiB** on the serving engine and
  fits comfortably in ~8–16 GB VRAM.
- **A default StorageClass** — this stack is storage‑hungry. PVCs: open‑webui (**20 Gi**), Milvus standalone
  (**50 Gi**), MinIO (**50 Gi**), plus etcd. Budget **~130 Gi+**.
  ```bash
  kubectl get storageclass          # exactly one should say "(default)"
  ```
- **An ingress controller** — Traefik (RKE2 default) or NGINX. Note its IngressClass name.
- **cert-manager** *(required for the HTTPS options; skippable only for the HTTP‑only quick start)*:
  ```bash
  kubectl get pods -n cert-manager  # controller / cainjector / webhook Running
  ```
- **Image pull access** to `dp.apps.rancher.io` (the `application-collection` secret) for the vLLM, Milvus,
  and open‑webui images.

---

## Certificate options at a glance

The chat UI is served over an Ingress. How you terminate TLS is the main decision:

| Option | TLS | Needs | Browser result | Best for |
|---|---|---|---|---|
| **1 - HTTP only** | none | nothing | "Not secure" label, no warning page | fastest demo / air‑gapped PoC |
| **2 - Self‑signed (default)** | cert‑manager self‑signed CA | cert-manager | one‑time "untrusted cert" warning | any cluster with cert‑manager |
| **3 - Let's Encrypt** | real trusted cert | cert-manager + a public DNS zone (e.g. Cloudflare DNS‑01) | green padlock | a real hostname you own |

> The `open-webui` value `global.tls.source` selects the mechanism: `suse-private-ai` (built‑in self‑signed via
> cert‑manager — **the blueprint default**), `secret` (bring‑your‑own / cluster‑issuer / none), or `letsEncrypt`.
>
> `global.tls.source` (whether the **chart** provisions cert-manager objects) is a separate knob from
> `ingress.tls` (HTTPS on the Ingress itself). And `ingress.class` must match your controller's IngressClass —
> a typo silently 404s the whole UI.

---

## Editing the blueprint in SUSE AI Factory

Deploy the **Simple Chatbot with RAG (vLLM and Milvus)** blueprint from the AI Factory catalog. To customize it,
open the blueprint and edit each app's values (`vllm`, `open-webui`, `milvus`, `open-webui-mcpo`) in the values
editor, then re‑deploy/upgrade.

![Edit the blueprint](../assets/Simple_Chatbot_with_RAG-edit-blueprint.gif)

**Everything below is expressed as changes to the shipped default values** — you only touch the keys shown.
Fields not mentioned keep their defaults (the RAG settings `VECTOR_DB: milvus`, `MILVUS_URI`, the MiniLM
embedding model, the OpenAI/vLLM wiring, signup, persistence, etc. are already set for you).

---

## Two open-webui settings you'll add (same in every option)

Two environment variables go in the **`open-webui`** app's values, inside its **`extraEnvVars`** list — the
same list that already contains `VECTOR_DB`, `MILVUS_URI`, the OpenAI wiring, etc. **Append them as new list
entries** (don't replace the existing ones). Unlike the ingress/TLS choice below, **these are identical for all
three options**:

- **`INSTALL_NLTK_DATASETS: "false"`** — the default `"true"` re-downloads NLTK data on every restart and can
  hang on GitHub rate-limits (a 429 will 500 the UI). Turn it off.
- **`TOOL_SERVER_CONNECTIONS`** — auto-registers the mcpo "memory" tool at boot, so no one adds it in the UI.
  open-webui fetches tool servers **from its backend pod**, so this points at the **internal Service**
  (`open-webui-mcpo:8000`) — same value in every option, **no NodePort or mcpo Ingress needed**. Always keep the
  **`/memory`** suffix.

```yaml
extraEnvVars:                        # append to the existing list — keep the entries already there
  - name: INSTALL_NLTK_DATASETS
    value: "false"
  - name: TOOL_SERVER_CONNECTIONS
    value: '[{"url":"http://open-webui-mcpo:8000/memory","path":"openapi.json","type":"openapi","auth_type":"bearer","headers":null,"key":"","config":{"enable":true,"function_name_filter_list":"","access_control":null},"spec_type":"url","spec":"","info":{"id":"","name":"memory","description":""}}]'
  # optional — also auto-listed from /v1/models:
  - name: DEFAULT_MODELS
    value: microsoft/Phi-3-mini-4k-instruct
```

> ⚠️ **`TOOL_SERVER_CONNECTIONS` must be a single-line, single-quoted string.** If the values editor pretty-prints
> it into nested YAML, the pod fails to create with `cannot unmarshal array into … EnvVar…value of type string`;
> a `>-` folded block silently injects spaces into the URL (`open-webui-␣␣␣mcpo`). Single quotes are required
> because the JSON uses double quotes.

---

## The model & tool calling

The blueprint serves **`microsoft/Phi-3-mini-4k-instruct`**, defined in `vllm` → `servingEngineSpec.modelSpec`
(model URL, `requestGPU` / CPU / memory, `runtimeClassName: nvidia`). It's great for the **chat** and **RAG**
demos as shipped.

> ⚠️ **Tool calling on vLLM needs more than a tool URL.** For the model to actually *invoke* the memory tool,
> vLLM's OpenAI server must have tool-calling enabled (`--enable-auto-tool-choice` + a `--tool-call-parser`
> matched to the model) **and** the model must support function calling. **Phi-3-mini is a weak tool-caller.**
> For a crisp MCPO tool demo, serve a tool-capable instruct model (e.g. a **Qwen2.5-Instruct**) and enable the
> matching parser (`hermes` for Qwen). Verify these flags against your `vllm` chart version — the RAG and chat
> demos work with Phi-3 unchanged.

---

## Option 1 — Quickest & easiest (no certs)

No cert‑manager, no cert plumbing. Set `global.tls.source: secret` and serve plain HTTP. Reach the UI **either**
way below — both skip TLS entirely. (The mcpo tool wiring is the internal Service, so there's nothing to do there;
`open-webui-mcpo` stays default in both.)

**1a — Ingress over HTTP** (you want a hostname)
```yaml
# open-webui
global:
  tls:
    source: secret                 # was suse-private-ai — no chart-managed cert
ingress:
  class: traefik                   # was "" — set your IngressClass
  host: suse-open-webui.example.local
  tls: false                       # was true — plain HTTP
  annotations: {}                  # drop the nginx ssl-redirect annotation
```
Point a hosts/DNS entry at the ingress node, then browse `http://suse-open-webui.example.local`:
```
<NODE_IP>  suse-open-webui.example.local
```

**1b — NodePort / LoadBalancer** (no ingress, no hostname, no DNS — the simplest path)
Expose the `open-webui` Service directly. No ingress means no TLS termination, so certs are moot:
```yaml
# open-webui
global:
  tls:
    source: secret                 # no chart-managed cert
ingress:
  enabled: false                   # optional — skip the ingress entirely
service:
  type: NodePort                   # browse http://<node-ip>:30080
  nodePort: 30080
  # …or  type: LoadBalancer        # browse http://<external-ip>/  — needs an LB provider (MetalLB, cloud, k3s/RKE2 svclb)
```

---

## Option 2 — Cluster with cert-manager (blueprint default)

Closest to the shipped defaults: keep `global.tls.source: suse-private-ai` and cert‑manager mints a self‑signed
cert automatically. HTTPS works with a one‑time "untrusted CA" browser warning. No public DNS needed.

**`open-webui` value changes** — only the host + IngressClass (plus the `extraEnvVars` above)
```yaml
ingress:
  class: traefik                   # was "" — set your IngressClass
  host: suse-open-webui.example.local
  # global.tls.source stays "suse-private-ai" (default) — no change
```
**`open-webui-mcpo`:** no changes.

**Reach it:** a hosts entry pointing at the ingress node, then browse `https://` (accept the cert once):
```
<NODE_IP>  suse-open-webui.example.local
```

---

## Option 3 — System like mine (Let's Encrypt already set up)

You have cert‑manager **and** a working ACME `ClusterIssuer` (e.g. `letsencrypt-prod` using **Cloudflare
DNS‑01**) for a domain you control. This yields a real, trusted certificate.

**`open-webui` value changes** (plus the `extraEnvVars` above)
```yaml
global:
  tls:
    source: secret                 # was suse-private-ai — see note below
ingress:
  class: traefik                   # was ""
  host: suse-open-webui.dna-42.com            # your FQDN
  tls: true                        # (default)
  existingSecret: suse-open-webui-tls          # was "" — cert-manager fills this
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod   # was the nginx ssl-redirect annotation
```
**`open-webui-mcpo`:** no changes.

> **Why `source: secret`?** With any other value the chart auto‑injects a second `cert-manager.io/issuer`
> annotation alongside your `cluster-issuer` — cert‑manager refuses both and issues nothing. `secret` leaves
> only your annotation, so ingress‑shim issues the real cert into `suse-open-webui-tls`.

**DNS:** create an A record for the host pointing at the ingress node IP. If the node IP is private
(e.g. `10.9.0.113`), use **DNS‑only** (grey cloud in Cloudflare) — DNS‑01 validation writes a TXT record
via the API, so the cert issues even though the host resolves to a private address.

**Watch issuance**
```bash
kubectl -n simple-chatbot-with-rag-vllm-and-milvus-system get certificate,order,challenge
# READY=True on the certificate → trusted cert served
```

> **DNS‑01 gotcha:** cert‑manager verifies the challenge TXT through its configured recursive resolver.
> If that's `8.8.8.8` and Google is slow/negative‑cached, the challenge can hang for minutes even though the
> record is live on Cloudflare. Since your zone is Cloudflare, point cert‑manager's self‑check at `1.1.1.1`:
> ```
> --dns01-recursive-nameservers-only=true
> --dns01-recursive-nameservers=1.1.1.1:53
> ```

---

## How the MCPO auto‑wiring works (and why the URL matters)

open‑webui loads OpenAPI tool servers **from its backend pod** (not the browser), so:

1. **The internal Service URL is enough** — `http://open-webui-mcpo:8000/memory`. No NodePort, no mcpo Ingress,
   and it's independent of how you expose the UI (HTTP or HTTPS). `open-webui-mcpo` keeps its default ClusterIP.
2. `TOOL_SERVER_CONNECTIONS` **pre‑registers** the tool at boot, so users never add it in the UI. The URL must
   include the **`/memory`** subpath, and the object must include `type: openapi` and `spec_type: url` — the exact
   shape shown above.
3. Keep **`INSTALL_NLTK_DATASETS: "false"`** — the NLTK download otherwise re‑runs on every restart and can hang
   on GitHub rate‑limits.

> Validated on this blueprint's `open-webui` (0.6.x). Older builds ran tool servers **from the browser** and
> required mcpo exposed via a NodePort/Ingress with a scheme matching the page — if you're on an older version,
> expose mcpo and use that browser‑reachable URL instead.

---

## Verify the deployment

```bash
NS=simple-chatbot-with-rag-vllm-and-milvus-system
kubectl -n $NS get pods
# vllm router + engine, milvus (+ etcd, + minio), open-webui-0, open-webui-mcpo all Running/Ready

# vLLM serving the model? (router exposes the OpenAI API)
kubectl -n $NS exec open-webui-0 -- curl -s http://vllm-router-service/v1/models       # -> Phi-3-mini

# mcpo tool spec loads from the backend?
kubectl -n $NS exec open-webui-0 -- \
  curl -s -o /dev/null -w '%{http_code}\n' http://open-webui-mcpo:8000/memory/openapi.json   # -> 200

# UI reachable?
curl -kI https://suse-open-webui.<your-domain>/     # -> HTTP 200
```

> **vLLM is slow on first start** — it downloads the model weights and compiles CUDA graphs (the engine's
> startup probe allows up to ~10 minutes). Watch `kubectl -n $NS logs <vllm-engine-pod>` until it prints
> "Application startup complete" before expecting chat to respond.

---

# Demo Instructions

### 0. First‑run setup
1. Open the chat URL. **The first account you create becomes the admin.**
2. Confirm **`Phi-3-mini-4k-instruct`** is selected in the model dropdown.
3. Send "hi" to warm the model — the first response after a cold start is the slowest.

### 1. RAG demo — grounded answers with citations
1. **Workspace → Knowledge → Create** a knowledge base named **"Event Horizon"**.
2. Upload the included **[`project_event_horizon_facility.pdf`](./project_event_horizon_facility.pdf)**.
3. Open a new chat, type **`#`** and select **Event Horizon** to attach it.
4. Ask the questions in the table — answers come back **with citations** (click them to show the retrieved text).
5. **The reveal:** ask the same question in a chat **without** the `#` knowledge base — the model doesn't know.
   Same model, one attaches your data, one doesn't. That contrast *is* the demo. (Embeddings live in Milvus.)

| Ask | Expected grounded answer |
|---|---|
| "When does the Event Horizon Data Center go fully online?" | June 15, 2030 (Phase VI commissioning) |
| "What energizes the core power grid?" | A micro-contained, localized black hole singularity anchored in Sublevel 4 |
| "What's the target noise level in the server rooms?" | Below 5 decibels under full compute load |
| "How much municipal water does the facility use?" | Zero — no additional water |
| "Why is the facility's exterior deep purple?" | A light-absorbent polymer for radiation shielding / thermal-signature obfuscation |

### 2. MCPO demo — the memory tool
1. In a chat, click the **🔧 tools icon** in the message bar and toggle **memory** on.
2. Say: *"Use the memory tool to remember that my favorite database is PostgreSQL and I work on the Orion team."*
3. Then: *"What do you know about me?"* — the bot calls the memory tool and recalls it from the knowledge graph.

> **Model note:** if the tool never fires, it's almost always the model/serving side, not the tool wiring
> (the Verify step already confirmed mcpo at 200). See **The model & tool calling** — Phi-3-mini is a weak
> tool-caller and vLLM needs `--enable-auto-tool-choice` + a matching `--tool-call-parser`.

---

## Sample RAG data — `project_event_horizon_facility.pdf`

The repo includes **[`project_event_horizon_facility.pdf`](./project_event_horizon_facility.pdf)** — a fictional
"Project Event Horizon" facility engineering spec (`EH-2030-FACILITY-V11`). It's packed with crisp, unique facts
a base model can't know — a black-hole singularity core power grid, sub-5-decibel server rooms, zero municipal
water, deep-purple radiation shielding, and a 4.2 ms Hawking-venting safety contingency — so grounded retrieval
is obvious and easy to verify. Upload it to the **Event Horizon** knowledge base in the RAG demo above.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| open-webui pod **fails to create**: `cannot unmarshal array into … EnvVar…value of type string` | `TOOL_SERVER_CONNECTIONS` entered as expanded YAML, not a string | Re-enter it as a **single-line, single-quoted** JSON string. |
| mcpo URL has **spaces** in the hostname (`open-webui-␣␣␣mcpo`) | a `>-` fold / line-wrap injected whitespace | Use the single-quoted one-liner; never fold this value. |
| **404** on the UI host | `ingress.class` ≠ your controller's IngressClass (e.g. `trarfik`) | Set `ingress.class` to your controller's class (`traefik`). |
| **"Failed to connect … OpenAPI tool server"** in the UI | wrong tool URL, or mcpo pod not ready | Use `http://open-webui-mcpo:8000/memory`; confirm the mcpo pod is Running. |
| Tool server added but **no tools appear** | URL missing the `/memory` subpath, so open‑webui loads the empty root spec | Use `…/memory` in the tool URL. |
| **Tool never fires** in chat (but Verify shows mcpo 200) | Model/serving side: Phi-3 weak at tools, or vLLM tool-call flags not set | Use a tool-capable model + `--enable-auto-tool-choice` / `--tool-call-parser`. |
| vLLM engine **Pending** / stays on CPU | `nvidia.com/gpu` not schedulable or no `nvidia` runtime class | Confirm the GPU Operator is installed, the node advertises `nvidia.com/gpu`, and `runtimeClassName: nvidia` is set. |
| vLLM **CUDA OOM** on start | Model too large for the GPU | Use a smaller model / quantization, or a bigger GPU; lower `--gpu-memory-utilization` if exposed. |
| Chat errors: **connection refused to `vllm-router-service`** | Router not ready or engine still loading weights | Wait for the engine startup probe; check engine logs for "Application startup complete". |
| **Milvus not ready** / RAG upload errors | etcd or MinIO PVC still Pending, or Milvus still initializing | `kubectl -n $NS get pvc,pods`; ensure a default StorageClass and ~130 Gi+ capacity. |
| UI returns **500 / redirects to `/error`** | `INSTALL_NLTK_DATASETS=true` hit a GitHub 429 and hangs | Set `INSTALL_NLTK_DATASETS: "false"` and restart. |
| Cert stuck **`Certificate READY=False`**, challenge pending | DNS‑01 self‑check resolver (`8.8.8.8`) not seeing the record | Point cert‑manager at `1.1.1.1` (see Option 3 note). |
| Pods **ImagePullBackOff** from `dp.apps.rancher.io` | No pull secret | Ensure the `application-collection` secret exists in the namespace, or set `global.imagePullSecrets`. |
| Browser **cert warning** on Options 1–2 | Expected (HTTP / self‑signed) | Use Option 3 for a trusted cert. |
