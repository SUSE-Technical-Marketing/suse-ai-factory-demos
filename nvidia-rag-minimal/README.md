# NVIDIA RAG (minimal, low-GPU)

A full **NVIDIA NIM-powered RAG** pipeline — document ingestion, embeddings, reranking, and generation, all served
by NVIDIA Inference Microservices — tuned to run on a **single ~24 GB GPU** (A10 / L4). One umbrella chart
(`nvidia-blueprint-rag` v2.6.0) deploys everything into the `nvidia-rag` namespace.

> ⚠️ **This is the heavyweight demo.** It needs a GPU and NVIDIA's NIM stack. If you just want to show RAG
> quickly, the [Simple Chatbot with RAG](../simple-chatbot-rag/README.md) runs on CPU.

## What you can demo
Same story as the chatbot RAG demo — upload a document, ask grounded questions, get **cited** answers, and watch it
*not* know the same facts without the doc — but on **NVIDIA's enterprise RAG stack**:

| Piece | NIM / service |
|---|---|
| **LLM** | `meta/llama-3.2-3b-instruct` (NIM) — swapped down from the default 49B Nemotron |
| **Embeddings** | `nvidia/llama-nemotron-embed-1b-v2` (NIM) |
| **Reranking** | `nvidia/llama-nemotron-rerank-1b-v2` (NIM) |
| **Ingestion** | `nv-ingest` (chunk + embed) |
| **Vector store** | Milvus **standalone** + MinIO + Redis (text-only) |
| **UI** | RAG Frontend at `rag-frontend.suse.demo` |

## What the "minimal, low-GPU" profile does
To fit a single ~24 GB GPU, the blueprint trims the full RAG stack:
- **Smaller LLM** — Llama 3.2 3B instead of 49B Nemotron.
- **Reclaims ~18 GB VRAM** — OCR, table, chart, and page-element extraction **off**; the vision LLM (VLM) and
  vision-embed NIMs **off**.
- **CPU vector search/index** (`APP_VECTORSTORE_ENABLEGPUSEARCH/INDEX: False`).
- **Milvus standalone**, text-only RAG.
- Trimmed token budget (`LLM_MAX_TOKENS: 1024`, `NIM_MAX_MODEL_LEN: 8192`, `NIM_KVCACHE_PERCENT: 0.15`).
- **Not production:** tracing/observability disabled; tuned for footprint, not throughput.

## Prerequisites
- **A single ~24 GB NVIDIA GPU** (A10 / L4) + the **GPU Operator** so the node advertises `nvidia.com/gpu`.
- **k8s-nim-operator** and **Elasticsearch eck-operator** installed (the blueprint requires both).
- **A default StorageClass** with room for the LLM model PVC (**35 Gi**) + Milvus + MinIO.
- Headroom on CPU/RAM (nv-ingest ~2 CPU / 4 Gi; Milvus standalone ~1 CPU / 2 Gi).

> **NGC credentials are handled for you.** SUSE AI Factory provisions the NGC secrets (`ngc-secret` for `nvcr.io`
> pulls, `ngc-api` for model weights) automatically — if you can see and deploy this blueprint, they're already set
> up. Nothing to create.

## Customize before you deploy
Clone the blueprint in AI Factory and edit the values, then deploy into the `nvidia-rag` namespace.

### Access — pick one
The RAG Frontend serves on the `rag-frontend` Service, port **3000**.

**Ingress (default).** Set the host to something that resolves to your ingress node:
```yaml
nimOperator:
  nim-llm:
    expose:
      ingress:
        enabled: true
        spec:
          rules:
            - host: rag-frontend.suse.demo   # change to your host
              http:
                paths:
                  - backend: { service: { name: rag-frontend, port: { number: 3000 } } }
                    path: /
                    pathType: Prefix
```
Add a hosts/DNS entry `<node-ip>  <your-host>` and browse `http://<your-host>`.
> The blueprint's built-in note says create DNS for `rag-frontend.suse.`**`com`**, but the ingress rule is
> `rag-frontend.suse.`**`demo`** — use `.demo` (or change both to match).

**NodePort / LoadBalancer (no ingress, no DNS).** Turn the ingress off and expose the Service directly:
```yaml
nimOperator:
  nim-llm:
    expose:
      ingress:
        enabled: false
```
Then set the `rag-frontend` Service to `NodePort` or `LoadBalancer` and browse the node/external IP on port 3000.
If the chart doesn't expose a service-type value, patch it after deploy:
```bash
kubectl -n nvidia-rag patch svc rag-frontend -p '{"spec":{"type":"NodePort"}}'
kubectl -n nvidia-rag get svc rag-frontend      # note the assigned nodePort → http://<node-ip>:<nodePort>
```

### Models (the low-GPU picks)
```yaml
envVars:
  APP_LLM_MODELNAME: meta/llama-3.2-3b-instruct
  APP_EMBEDDINGS_MODELNAME: nvidia/llama-nemotron-embed-1b-v2
  APP_RANKING_MODELNAME: nvidia/llama-nemotron-rerank-1b-v2
```
**More GPU to spend?** Scale the demo up by re-enabling what the minimal profile turned off:
- `nimOperator.nim-vlm.enabled: true` (vision LLM)
- `nv-ingest` extraction: `APP_NVINGEST_EXTRACTTABLES/EXTRACTCHARTS: True`, and the `nv-ingest.nimOperator` OCR /
  page-element / table-structure NIMs.
- `APP_VECTORSTORE_ENABLEGPUSEARCH/ENABLEGPUINDEX: True`, a larger LLM, higher `NIM_KVCACHE_PERCENT`.

## Deploy & verify
Deploy the blueprint into `nvidia-rag`, then — NIMs **download multi-GB model weights on first start**, so this is
slow:
```bash
NS=nvidia-rag
kubectl -n $NS get pods
# expect: nim-llm, the embed + rerank NIMs, rag-nv-ingest, milvus, rag-minio, rag-redis, rag-server, rag-frontend

# NIMs ready? (they stay 0/1 while pulling weights)
kubectl -n $NS get pods -l app.kubernetes.io/name=nim-llm

# UI reachable?
curl -I http://<your-host>/        # HTTP 200
```

## Run the demo
1. Browse to the RAG Frontend (`http://<your-host>`, or the NodePort/LB address).
2. Upload **[`project_event_horizon_facility.pdf`](../simple-chatbot-rag/project_event_horizon_facility.pdf)**
   (the shared sample doc) — nv-ingest chunks + embeds it into Milvus.
3. Ask the questions below — answers come back grounded in the document, with citations.
4. **The reveal:** ask the same question with the document removed/unselected — the model doesn't know. Same model,
   one has your data, one doesn't. That contrast *is* the demo.

| Ask | Expected grounded answer |
|---|---|
| "When does the Event Horizon Data Center go fully online?" | June 15, 2030 (Phase VI commissioning) |
| "What energizes the core power grid?" | A micro-contained, localized black hole singularity anchored in Sublevel 4 |
| "What's the target noise level in the server rooms?" | Below 5 decibels under full compute load |
| "How much municipal water does the facility use?" | Zero — no additional water |
| "Why is the facility's exterior deep purple?" | A light-absorbent polymer for radiation shielding / thermal-signature obfuscation |

> 🎥 **Video:** _add the walkthrough link here._

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| NIM pods **ImagePullBackOff** from `nvcr.io` | NGC pull secret missing (shouldn't happen — AI Factory provisions it) | confirm the blueprint deployed through AI Factory; check `ngc-secret` exists in `nvidia-rag` |
| NIM pods **stuck 0/1** for a long time | downloading multi-GB model weights on first boot | wait; ensure the 35 Gi PVC bound and the node has disk |
| NIM **CUDA / VRAM OOM** | GPU < ~24 GB, or too much enabled | keep the minimal profile; don't re-enable VLM / extraction on a small GPU |
| Pods **Pending** — `nvidia.com/gpu` unschedulable | GPU Operator missing | install the GPU Operator; confirm the node advertises `nvidia.com/gpu` |
| NIM resources **never reconcile** | `k8s-nim-operator` not installed | install the NIM operator (prerequisite) |
| Deploy errors referencing Elasticsearch | `eck-operator` not installed | install the Elasticsearch ECK operator (prerequisite) |
| **404** on the UI host | ingress host/class mismatch, or no DNS entry | match the ingress `host`, set the IngressClass, add the hosts/DNS record |
