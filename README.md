# Bird Inference API

API de inferência de aves com FastAPI e TensorFlow.

## Objetivo

Servir predições de classe para imagens, carregando `model.keras` e `classes.txt` via S3/MinIO no startup.

## Funcionalidades

- Endpoint de saúde (`/health`) com status dos artefatos.
- Endpoint de predição (`/predict`) para upload de imagem.
- Download obrigatório de artefatos no startup.
- Logs separados por contexto (`InferenceAPI`, `Predictor`, `S3Artifacts`).

## Estrutura

- `app/app.py`: inicialização da API e rotas.
- `app/services/predictor.py`: pré-processamento e inferência.
- `app/utils/utils_s3.py`: download de `model.keras` e `classes.txt` no S3/MinIO.
- `app/utils/logger.py`: configuração de logger com rotação.
- `docker-compose.yml`: execução do serviço com `uvicorn`.
- `pyproject.toml`: dependências Python gerenciadas com Poetry.

## Pré-requisitos

- Docker + Docker Compose.
- Acesso ao bucket S3/MinIO.

## Configuração

1. Crie o arquivo de ambiente:

```bash
cp .env.example .env
```

2. Ajuste as variáveis no `.env`.

## Variáveis de ambiente

- `API_PORT`: porta interna da API (default `8001`).
- `MODEL_PATH`: caminho local do modelo (default `app/data/model.keras`).
- `CLASSES_PATH`: caminho local das classes (default `app/data/classes.txt`).
- `MINIO_URL`: endpoint S3/MinIO.
- `MINIO_ROOT_USER`: access key.
- `MINIO_ROOT_PASSWORD`: secret key.
- `S3_BUCKET`: bucket dos artefatos.
- `S3_MODEL_KEY`: chave do `model.keras` no bucket.
- `S3_CLASSES_KEY`: chave do `classes.txt` no bucket.
- `BIRD_DOMAIN`: host usado no label do Traefik.
- `TRAEFIK_NET`: rede externa do Traefik.

## Executar com Docker

```bash
docker compose up --build -d
```

Para acompanhar logs:

```bash
docker compose logs -f bird-api
```

## Executar sem Docker

```bash
poetry install
uvicorn app.app:app --host 0.0.0.0 --port 8001
```

## Endpoints

### `GET /health`

Resposta quando pronto:

```json
{
  "status": "ok",
  "missing_artifacts": []
}
```

Resposta quando faltam artefatos:

```json
{
  "status": "waiting_artifacts",
  "missing_artifacts": ["app/data/model.keras", "app/data/classes.txt"]
}
```

### `POST /predict`

Envia imagem multipart:

```bash
curl -X POST "http://localhost:8001/predict" \
  -F "file=@/caminho/para/imagem.jpg"
```

Resposta de sucesso:

```json
{
  "class_id": 1,
  "class_name": "Black footed Albatross",
  "confidence": 0.9876
}
```

Erros esperados:

- `400`: arquivo enviado não é imagem.
- `503`: artefatos ausentes.
- `500`: erro interno no processamento.

## Fluxo de artefatos S3

- No startup, a API chama `download_inference_artifacts_from_env`.
- Se configuração S3 estiver incompleta, o startup falha.
- Se o download falhar, o startup falha.
- Se o arquivo já existir localmente e `overwrite=false`, não baixa novamente.

## Formato esperado de `classes.txt`

Arquivo com separador por espaço no padrão:

```text
1 001.Black_footed_Albatross
2 002.Laysan_Albatross
```

## Logs

Os logs são gravados em `app/logs/`:

- `InferenceAPI.log`
- `Classifier.log`
- `S3Artifacts.log`

## Segurança

- Não versione `.env` com segredo real.
- Use `.env.example` como template.
- Rotacione credenciais já expostas anteriormente.
