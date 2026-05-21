# Setup em máquina nova

Guia completo pra continuar o desenvolvimento do **InsurMind Chatbot** em outra máquina Windows. Suporta 2 caminhos de migração:

- **Caminho A — Clone do GitHub** (do zero, máquina realmente virgem). Mais lento mas robusto. Veja "Etapa 1" em diante.
- **Caminho B — Cópia da pasta via rede** (se a máquina antiga está acessível). Mais rápido, preserva `.git/`, `.env`, `.chroma/`. Veja "Caminho B" logo abaixo.

> ✅ Pré-requisito (qualquer caminho): o cleanup pré-entrega foi commitado e empurrado pro GitHub (verifique se `git status` na máquina antiga mostra "nothing to commit, working tree clean" antes de migrar).

---

## Caminho B — Migração via cópia da pasta (rápida)

Se você vai copiar a pasta inteira via rede / OneDrive / USB, este é o atalho. Bate em ~15-20 min em vez de 60-90 min.

### B.1 — Na máquina ATUAL, antes de copiar

Algumas pastas **não migram limpas** (paths absolutos hardcoded ou binários nativos). Deletar antes de copiar evita problemas e reduz drasticamente o tamanho da transferência:

```powershell
# Vá pra raiz do projeto
cd C:\Bruno\OneDrive` - Rede D'Or\05.Pessoal\Projetos\i2a2\insurminds\chatbot

# Deletar pastas que NÃO migram bem (regeneráveis na máquina nova):
Remove-Item -Recurse -Force .venv              # virtualenv Python (~1.8GB, paths hardcoded)
Remove-Item -Recurse -Force web\node_modules   # binários nativos podem quebrar (~500MB)
Remove-Item -Recurse -Force web\.next          # build cache do Next.js
```

**Tamanho economizado**: ~2.3GB. Restante da pasta deve estar em ~50MB.

**Pastas que migram OK** (não delete):
- `.git/` — histórico + remotes + credentials cache → economiza muito tempo
- `.chroma/` — ~10MB, apenas SQLite + parquet, paths internos relativos
- `.env` — secrets que você não quer reconfigurar
- `data/`, `src/`, `web/app`, `web/components`, etc. — arquivos do projeto

### B.2 — Copiar via rede

Use o método que preferir (drag-and-drop pelo Explorer, robocopy, scp, etc.). Destino na máquina nova:

```
C:\Bruno\<outra pasta>\05.Pessoal\Projetos\i2a2\insurminds\chatbot
```

> 💡 Dica do `robocopy` (mais rápido e robusto que copiar pelo Explorer):
> ```powershell
> robocopy "\\PC-ANTIGO\Projetos\i2a2\insurminds\chatbot" "C:\Bruno\Local\05.Pessoal\Projetos\i2a2\insurminds\chatbot" /E /MT:16 /R:2 /W:2 /XD .venv node_modules .next
> ```

### B.3 — Na máquina NOVA, instalar softwares base

Veja **Etapa 1** abaixo (Git, Python 3.12, Node LTS, Claude Code). Os outros itens da Etapa 1 ainda se aplicam.

### B.4 — Na máquina NOVA, dentro da pasta copiada

```powershell
cd C:\Bruno\<outra pasta>\05.Pessoal\Projetos\i2a2\insurminds\chatbot

# Verifica que o .git veio na cópia (remotes preservados):
git remote -v
# Deve mostrar 'origin' (GitHub) e 'hf' (HuggingFace Space)

git status
# Provavelmente vai mostrar working tree clean (estado preservado)

# Recriar virtualenv Python (path velho era da máquina antiga)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e ".[dev,dataprep]"

# .chroma/ já veio copiada — só verifica que está OK:
python -c "from insurmind.rag import _get_collection; _get_collection(); print('Chroma OK')"

# Recriar node_modules
cd web
npm install
cd ..
```

### B.5 — Smoke test

```powershell
python -m insurmind.agent "O que é franquia?"
```

Se responder corretamente em 10-30s, **migração via cópia validada** ✅. Pule pra "Etapa 6" abaixo se quiser validar a UI completa.

**Total estimado do Caminho B**: 15-20 min (10 min copy via rede + 5 min `pip install` + 2 min `npm install` + smoke test).

---

## Caminho A — Setup do zero via git clone

> Use este caminho se a máquina antiga não está acessível ou prefere setup limpo. Tempo total: 60-90 min.

### Visão geral

| Etapa | O que faz | Tempo aprox. |
|---|---|---|
| 1 | Instalar softwares base (Git, Python, Node, Claude Code) | 20-30 min |
| 2 | Configurar autenticação (GitHub + HuggingFace) | 10 min |
| 3 | Clonar o repo e configurar `.env` | 5 min |
| 4 | Instalar dependências Python + ingerir KB | 15 min (1ª vez baixa modelo ~500MB) |
| 5 | Instalar dependências Node + buildar UI | 5-10 min |
| 6 | Smoke test (verificar que tudo funciona) | 5 min |

**Total estimado**: 60-90 min do zero ao chatbot rodando.

---

## Etapa 1 — Instalação de softwares base

Use o **Winget** (gerenciador de pacotes nativo do Windows 10/11) pra instalar tudo via terminal. Abra o **PowerShell como Administrador**:

### 1.1 Git for Windows

```powershell
winget install --id Git.Git -e --source winget
```

Após instalar, **feche e reabra o terminal** pra o PATH atualizar.

Configurar identidade git (importante pra commits funcionarem):

```powershell
git config --global user.name "Bruno Couto Veiga"
git config --global user.email "brunocoutoveiga@gmail.com"
git config --global init.defaultBranch main
git config --global core.autocrlf true  # converte EOL no Windows
```

### 1.2 Python 3.12

```powershell
winget install --id Python.Python.3.12 -e --source winget
```

Verifica:

```powershell
python --version  # esperado: Python 3.12.x
pip --version
```

> Versão atual da máquina de origem: **Python 3.12.10**. Qualquer 3.12.x serve. Não use 3.13 ainda — algumas libs (sentence-transformers) podem não estar 100% testadas nele.

### 1.3 Node.js LTS

```powershell
winget install --id OpenJS.NodeJS.LTS -e --source winget
```

Verifica:

```powershell
node --version  # esperado: v22.x ou v24.x
npm --version
```

> Máquina de origem está em **Node v24.15.0**. Qualquer LTS recente (v20+) serve.

### 1.4 Claude Code (recomendado)

Você usou Claude Code durante todo o desenvolvimento — vale instalar pra continuar com o mesmo workflow.

```powershell
# Pelo instalador oficial
winget install --id Anthropic.Claude -e --source winget
```

Ou direto via npm (alternativa):

```powershell
npm install -g @anthropic-ai/claude-code
```

Login com sua conta Anthropic na primeira execução.

### 1.5 (Opcional) VSCode

```powershell
winget install --id Microsoft.VisualStudioCode -e --source winget
```

Extensões úteis pro projeto:

```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension anthropic.claude-code
```

### 1.6 (Opcional) Docker Desktop

Necessário **só se** quiser testar o build do container Docker localmente (mesmo que vai pro HF Spaces). Pra dev normal, não precisa.

```powershell
winget install --id Docker.DockerDesktop -e --source winget
```

---

## Etapa 2 — Autenticação (GitHub + HuggingFace)

### 2.1 GitHub — Personal Access Token

Necessário pra `git push origin main` funcionar.

1. Acesse https://github.com/settings/tokens
2. **Generate new token** → **Generate new token (classic)**
3. Note: "InsurMind dev" / Expiration: 90 dias / Scopes: marca `repo`
4. **Generate token** → **copia o token** (formato `ghp_...`)

Na primeira vez que você fizer `git push`, o terminal vai pedir credenciais. Usa:
- Username: `BrunoCoutoVeiga`
- Password: cola o token (não a senha do GitHub)

O Git Credential Manager (vem com Git for Windows) vai salvar pra reutilizar.

### 2.2 HuggingFace — Write Token

Necessário pra `git push hf main` (deploy do backend).

1. Acesse https://huggingface.co/settings/tokens
2. **+ Create new token**
3. Token name: `insurmind-deploy` / Token type: **Write**
4. **Create token** → **copia**

Salva esse token — vai ser usado na primeira vez que fizer push pro HF.

### 2.3 Anthropic API Key

Mesma chave usada na máquina antiga. Pode buscar em:

- Console Anthropic: https://console.anthropic.com/settings/keys (se ainda tem acesso à chave salva)
- OU criar uma nova chave (recomendado se você não salvou a anterior)

Anota a chave (`sk-ant-api03-...`).

### 2.4 (Opcional) Gemini API Key

A chave Gemini é alternativa free pra desenvolvimento. Você tem uma em `.env` da máquina antiga.

- Console: https://aistudio.google.com/apikey
- Free tier: 15 req/min, 1500 req/dia — sobra pra dev

---

## Etapa 3 — Clonar o repo e configurar `.env`

Abre o **PowerShell normal** (não administrador) e navega pra onde quer guardar o projeto:

```powershell
# Crie pasta de projetos se ainda não tem
mkdir C:\Bruno\Projetos -ErrorAction SilentlyContinue
cd C:\Bruno\Projetos

# Clona o repo público
git clone https://github.com/BrunoCoutoVeiga/i2a2-insurminds-chatbot-cotacao-seguro-auto.git
cd i2a2-insurminds-chatbot-cotacao-seguro-auto
```

### Configurar o `.env`

Copia o template e edita:

```powershell
cp .env.example .env
notepad .env
```

Preenche assim (substitua `<...>` pelos valores reais):

```
INSURMIND_LLM=anthropic_api
ANTHROPIC_API_KEY=<sua_chave_anthropic_aqui>
GEMINI_API_KEY=<sua_chave_gemini_aqui_se_tiver>
GEMINI_MODEL=gemini-2.5-flash
```

Salva e fecha.

> ⚠️ `.env` está no `.gitignore` — nunca vai pro git. Tá seguro.

### Adicionar o remote do HuggingFace

O clone do GitHub só cria o remote `origin`. Pra push pro HF Space também:

```powershell
git remote add hf https://huggingface.co/spaces/bveiga/insurminds-api
git remote -v
```

Deve mostrar 2 remotes: `origin` e `hf`.

---

## Etapa 4 — Setup do backend Python

```powershell
# Cria virtualenv isolada
python -m venv .venv

# Ativa
.\.venv\Scripts\Activate.ps1
```

> ⚠️ Se der erro `não pode ser executado` no `Activate.ps1`, rode antes (1x só):
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Instala dependências do projeto:

```powershell
pip install --upgrade pip
pip install -e ".[dev,dataprep]"
```

`-e` = editable install (mudanças no `src/` ficam vivas sem reinstalar).
`[dev,dataprep]` = extras opcionais (pytest pra testes, pypdf pra re-extrair PDFs caso queira).

Tempo: ~3-5 min na primeira vez (baixa torch ~250MB).

### Ingerir a KB no Chroma

```powershell
python scripts/ingest_kb.py
```

Tempo:
- **Primeira vez**: ~3-5 min (baixa modelo e5-base ~500MB do HuggingFace + embed 312 chunks)
- **Vezes seguintes**: ~10-30s (modelo fica cached em `~/.cache/huggingface/`)

Saída esperada (último trecho):

```
Total: 312 chunks ingeridos em insurmind_kb
Distribuição por source:
  fenacor           24
  porto-cg         177
  porto-faq         53
  porto-glossario   14
  susep-cartilha    32
  susep-glossario   12
Banco persistido em .chroma/ — pronto pra retrieval.
```

### Smoke test do agente (sem UI)

```powershell
python -m insurmind.agent "O que é franquia?"
```

Deve responder em ~10-30s com explicação sobre franquia + citação de fonte da Porto Inseguro. Se vier resposta coerente, **backend tá OK**.

---

## Etapa 5 — Setup do frontend Next.js

Em outro terminal (o backend não precisa estar rodando ainda):

```powershell
cd C:\Bruno\Projetos\i2a2-insurminds-chatbot-cotacao-seguro-auto\web
npm install
```

Tempo: ~2-3 min.

### Variável de ambiente do frontend

Por default o frontend chama `http://127.0.0.1:8000` (backend local). Se quiser que aponte pra produção, cria `.env.local`:

```powershell
cp .env.example .env.local
notepad .env.local
```

E edita pra:

```
# Pra dev local apontando pro backend local:
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

# OU pra dev local apontando pro HF Spaces de produção:
# NEXT_PUBLIC_API_BASE=https://bveiga-insurminds-api.hf.space
```

---

## Etapa 6 — Smoke test completo (UI funcionando)

### Subir o backend

No terminal do venv ativado:

```powershell
uvicorn insurmind.api:app --port 8000 --reload
```

Aguarda ver `Uvicorn running on http://0.0.0.0:8000`.

### Subir o frontend

Em outro terminal:

```powershell
cd C:\Bruno\Projetos\i2a2-insurminds-chatbot-cotacao-seguro-auto\web
npm run dev
```

Aguarda ver `Local: http://localhost:3000`.

### Testar no browser

1. Abre http://localhost:3000
2. Header deve mostrar `anthropic_api · 3 tools`
3. Pergunta "o que é prêmio?" — deve responder em 30-60s (primeira vez) ou 5-10s (subsequentes)
4. Verifica o painel debug mostrando os 10 passos do agente

**Se tudo isso funcionou, migração completa ✅**

---

## Bônus — Sua RTX 5060 Ti de 16GB

Hoje o projeto usa **CPU pra embeddings** (modelo e5-base em fp16, ~236MB de RAM). Funciona bem mas demora 10-15s pra embedar uma query.

Com sua **GPU de 16GB**, dá pra rodar:
- **e5-base em fp32 na GPU** — ~1GB de VRAM, mas inferência **~10x mais rápida**
- **Modelos maiores** — `e5-large` (~2GB) ou `bge-m3` (~2GB) com qualidade superior

Pra ativar GPU, instalar PyTorch com CUDA:

```powershell
# Desinstala torch CPU-only
pip uninstall torch -y

# Instala torch com CUDA 12.x (que casa com sua RTX 5060 Ti)
pip install torch --index-url https://download.pytorch.org/whl/cu124

# Verifica
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# Esperado: True NVIDIA GeForce RTX 5060 Ti
```

Depois, em `src/insurmind/rag.py`, no `_get_model()`:

```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
_model = SentenceTransformer(EMBED_MODEL_NAME, device=device, ...)
```

E pode tirar o `INSURMIND_FP32=1` (com 16GB de VRAM, fp32 cabe folgado).

> ⚠️ Importante: **só faça isso se quiser otimizar**. Pro projeto entregue, CPU+fp16 já funciona em produção (HF Spaces) e local. GPU é melhoria pra dev rápido.

---

## Troubleshooting

### `.venv\Scripts\Activate.ps1 cannot be loaded`

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `pip install` falha com permission denied

Não rode `pip install` como Administrador. Use o terminal normal com o venv ativo.

### `Modulo 'sentence_transformers' not found` no primeiro `ingest_kb.py`

Confirma que ativou o venv: `.\.venv\Scripts\Activate.ps1`. Deve ter `(.venv)` no prompt.

### `ANTHROPIC_API_KEY não configurada` ao rodar agente

Confirma `.env` na raiz do projeto + valor preenchido. O `load_dotenv` em `api.py` lê automático.

### Frontend não chama o backend

Verifica `NEXT_PUBLIC_API_BASE` em `web/.env.local` apontando pra URL correta (localhost:8000 em dev). Lembra que `NEXT_PUBLIC_*` é **embutida no build** — após mudar, rebuilda (`Ctrl+C` + `npm run dev`).

### Push pro HF Space pede credenciais e não aceita senha

HF não aceita senha tradicional. Use o **Write token** que você gerou em https://huggingface.co/settings/tokens.

---

## Checklist final de validação

- [ ] `git status` → "working tree clean"
- [ ] `git remote -v` → mostra `origin` (GitHub) e `hf` (HuggingFace)
- [ ] `.env` existe na raiz com `ANTHROPIC_API_KEY` preenchida
- [ ] `.chroma/` existe (gerado pelo `ingest_kb.py`)
- [ ] `python -m insurmind.agent "ola"` → responde
- [ ] `uvicorn insurmind.api:app --port 8000` → sobe
- [ ] `curl http://localhost:8000/api/health` → `{"status":"ok",...}`
- [ ] `cd web && npm run dev` → sobe em :3000
- [ ] http://localhost:3000 → chatbot funciona, pergunta de RAG retorna resposta com fonte

Se todos checados, **você está oficialmente migrado**. Boa continuidade do dev!

---

## URLs importantes pra ter no bookmark

- **Demo ao vivo (produção)**: https://insurminds-chatbot.vercel.app
- **Backend (produção)**: https://bveiga-insurminds-api.hf.space
- **Repo GitHub**: https://github.com/BrunoCoutoVeiga/i2a2-insurminds-chatbot-cotacao-seguro-auto
- **HF Space (Docker)**: https://huggingface.co/spaces/bveiga/insurminds-api
- **Dashboard Vercel**: https://vercel.com/dashboard
- **Dashboard HuggingFace**: https://huggingface.co/spaces/bveiga/insurminds-api/settings
- **Console Anthropic** (limites, uso, chaves): https://console.anthropic.com
