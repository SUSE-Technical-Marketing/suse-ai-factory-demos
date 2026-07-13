# Simple Chatbot with RAG (ollama) — QuickStart

`ollama` + `open-webui` (Chroma RAG) + `open-webui-mcpo` (`memory` tool). CPU.
Namespace `simple-chatbot-with-rag-system`. Full guide: [README.md](./README.md).

## Changes
| App | Set | Why |
|---|---|---|
| `ollama` | `models.pull` / `models.run` → `[qwen2.5:3b]` | `gemma:2b` can't tool-call; must match `DEFAULT_MODELS` |
| `open-webui` | `DEFAULT_MODELS: qwen2.5:3b` | UI default model |
| `open-webui` | `INSTALL_NLTK_DATASETS: "false"` | default `"true"` re-downloads NLTK each boot; hangs on GitHub 429 |
| `open-webui` | add `TOOL_SERVER_CONNECTIONS` (below) | pre-registers the mcpo `memory` tool at boot |
| `open-webui-mcpo` | — | defaults |

`open-webui` → `extraEnvVars`, **one line, single-quoted**:
```yaml
- name: TOOL_SERVER_CONNECTIONS
  value: '[{"url":"http://open-webui-mcpo:8000/memory","path":"openapi.json","type":"openapi","auth_type":"bearer","headers":null,"key":"","config":{"enable":true,"function_name_filter_list":"","access_control":null},"spec_type":"url","spec":"","info":{"id":"","name":"memory","description":""}}]'
```

## Access — `open-webui` only (`ingress.class` must match your controller)
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
- `global.tls.source` (cert-manager provisioning) ≠ `ingress.tls` (HTTPS on/off).
- `ingress.class` typo = silent 404. Only `open-webui` has a live Ingress.

## Verify
```bash
NS=simple-chatbot-with-rag-system
kubectl -n $NS get pods
kubectl -n $NS exec deploy/ollama -- ollama list                                     # qwen2.5:3b
kubectl -n $NS exec open-webui-0 -- curl -s -o /dev/null -w '%{http_code}\n' \
  http://open-webui-mcpo:8000/memory/openapi.json                                    # 200
curl -kI https://<host>/                                                              # 200
```
First account = admin. Chat → 🔧 → toggle **memory**.
