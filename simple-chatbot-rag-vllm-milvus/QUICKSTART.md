# Simple Chatbot with RAG (vLLM + Milvus) — QuickStart

`vllm` (OpenAI API) + `open-webui` (Milvus RAG) + `milvus` + `open-webui-mcpo` (`memory` tool). **GPU required.**
Namespace `simple-chatbot-with-rag-vllm-and-milvus-system`. Full guide: [README.md](./README.md).

Preset — don't touch: `OPENAI_API_BASE_URL: http://vllm-router-service/v1`, `VECTOR_DB: milvus`, `MILVUS_URI: http://milvus:19530`.

## Changes
| App | Set | Why |
|---|---|---|
| `vllm` | confirm `servingEngineSpec.modelSpec` (model, `requestGPU`), `runtimeClassName: nvidia` | GPU sizing / model |
| `open-webui` | `INSTALL_NLTK_DATASETS: "false"` | default `"true"` re-downloads NLTK each boot; hangs on GitHub 429 |
| `open-webui` | add `TOOL_SERVER_CONNECTIONS` (below) | pre-registers the mcpo `memory` tool at boot |
| `open-webui` | `DEFAULT_MODELS: microsoft/Phi-3-mini-4k-instruct` (optional) | UI default; also auto-listed from `/v1/models` |
| `milvus`, `open-webui-mcpo` | — | defaults (check Milvus storage sizing) |

`open-webui` → `extraEnvVars`, **one line, single-quoted**:
```yaml
- name: TOOL_SERVER_CONNECTIONS
  value: '[{"url":"http://open-webui-mcpo:8000/memory","path":"openapi.json","type":"openapi","auth_type":"bearer","headers":null,"key":"","config":{"enable":true,"function_name_filter_list":"","access_control":null},"spec_type":"url","spec":"","info":{"id":"","name":"memory","description":""}}]'
```

## Access — `open-webui` only, host `suse-open-webui.<domain>` (`ingress.class` must match your controller)
| Option | Set |
|---|---|
| HTTP (ingress) | `class`, `host`, `tls: false`, `global.tls.source: secret`, drop `ssl-redirect` |
| NodePort / LB (no certs, no ingress) | `service.type: NodePort` (`nodePort: 30080`) or `LoadBalancer`; `global.tls.source: secret`; `ingress.enabled: false` |
| self-signed (default) | `class`, `host` (keep `source: suse-private-ai`) |
| Let's Encrypt | `source: secret`, `existingSecret`, annotation `cert-manager.io/cluster-issuer` |

## Gotchas
- `TOOL_SERVER_CONNECTIONS`: one line, single-quoted. YAML-expanded → `unmarshal array … value of type string`; a `>-` fold adds spaces to the URL. Keep `/memory`.
- Tool specs are backend-fetched → internal Service URL works; no NodePort / mcpo Ingress.
- `TOOL_SERVER_CONNECTIONS` / `DEFAULT_MODELS` are PersistentConfig — seed only on a fresh PVC.
- `global.tls.source` (cert-manager provisioning) ≠ `ingress.tls` (HTTPS on/off). `ingress.class` typo = silent 404.
- GPU required; ~130 Gi+ storage; vLLM first start is slow (weights + CUDA graphs).
- Tool calling needs a tool-capable model + engine flags `--enable-auto-tool-choice` / `--tool-call-parser` (Phi-3 is weak; RAG/chat fine).

## Verify
```bash
NS=simple-chatbot-with-rag-vllm-and-milvus-system
kubectl -n $NS get pods
kubectl -n $NS exec open-webui-0 -- curl -s http://vllm-router-service/v1/models      # Phi-3-mini
kubectl -n $NS exec open-webui-0 -- curl -s -o /dev/null -w '%{http_code}\n' \
  http://open-webui-mcpo:8000/memory/openapi.json                                     # 200
curl -kI https://suse-open-webui.<domain>/                                            # 200
```
First account = admin. Chat → 🔧 → toggle **memory**.
