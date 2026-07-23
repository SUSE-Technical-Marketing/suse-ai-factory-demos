# NVIDIA RAG (minimal, low-GPU)

A full **NVIDIA NIM-powered RAG** pipeline — document ingestion, embeddings, reranking, and generation, all served
by NVIDIA Inference Microservices — tuned to run on a **single ~24 GB GPU** (A10 / L4). One umbrella chart
(`nvidia-blueprint-rag` v2.6.0) deploys everything.

> ⚠️ **This is the heavyweight demo.** It needs a GPU, NGC access, and two operators (NIM + Elasticsearch ECK). If
> you just want to show RAG quickly, the [Simple Chatbot with RAG](../simple-chatbot-rag/README.md) runs on CPU.

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
- **NGC access** — these secrets must already exist in the target namespace (the blueprint has `create: false`):
  - `ngc-secret` — image pull secret for `nvcr.io`.
  - `ngc-api` — your NGC API key (the NIMs use it to pull model weights).
  > Confirm these come from your NGC credentials / AI Factory NVIDIA secret setup.
- **k8s-nim-operator** installed — manages the NIM deployments.
- **Elasticsearch eck-operator** installed.
- **A default StorageClass** with room for the LLM model PVC (**35 Gi**) + Milvus + MinIO.
- Headroom on CPU/RAM (nv-ingest requests ~2 CPU / 4 Gi; Milvus standalone ~1 CPU / 2 Gi).

## Customize before you deploy
Copy the blueprint in AI Factory and edit the values, then deploy.

### Access (ingress host)
The RAG Frontend is exposed via ingress. Set the host to something that resolves to your ingress node:
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
Then add a hosts/DNS entry `<node-ip>  <your-host>` and browse `http://<your-host>`.
> The blueprint's built-in note says to create DNS for `rag-frontend.suse.**com**`, but the ingress rule is
> `rag-frontend.suse.**demo**` — use `.demo` (or change both to match).

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
Deploy the blueprint, then (NIMs **download multi-GB model weights on first start** — this is slow):



## Run the demo
1. Browse to `http://<your-host>` (the RAG Frontend).
2. Upload a document (nv-ingest chunks + embeds it into Milvus).
3. Ask questions grounded in the document — answers come back with citations.
4. **The reveal:** ask something the base model can't know without the doc, then remove/omit the doc and watch it
   lose the fact. Same contrast as the chatbot RAG demo.

> 🎥 **Video:** _add the walkthrough link here._

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| NIM pods **ImagePullBackOff** from `nvcr.io` | missing/invalid `ngc-secret` | create the NGC image-pull secret in the namespace |
| NIM pods **stuck 0/1** for a long time | downloading multi-GB model weights on first boot | wait; ensure the 35 Gi PVC bound and the node has disk |
| NIM **CUDA / VRAM OOM** | GPU < ~24 GB, or too much enabled | keep the minimal profile; don't re-enable VLM / extraction on a small GPU |
| Pods **Pending** — `nvidia.com/gpu` unschedulable | GPU Operator missing | install the GPU Operator; confirm the node advertises `nvidia.com/gpu` |
| NIM resources **never reconcile** | `k8s-nim-operator` not installed | install the NIM operator (a prerequisite) |
| Deploy errors referencing Elasticsearch | `eck-operator` not installed | install the Elasticsearch ECK operator (a prerequisite) |
| **404** on the UI host | ingress host/class mismatch, or no DNS entry | match the ingress `host`, set the IngressClass, add the hosts/DNS record |
