from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils.logger import LoggerConfig

logger = LoggerConfig(
    name="S3Artifacts", log_dir="logs", log_file="S3Artifacts.log"
).get_logger()


@dataclass
class S3ArtifactsDownloader:
    """Cliente para download de artefatos de inferência no S3/MinIO."""

    endpoint_url: str
    access_key: str
    secret_key: str
    bucket: str
    model_key: str = "model.keras"
    classes_key: str = "classes.txt"

    @classmethod
    def from_env(cls) -> S3ArtifactsDownloader | None:
        """Cria o downloader a partir de variáveis de ambiente."""
        endpoint_url = os.getenv("MINIO_URL", "").strip()
        access_key = os.getenv("MINIO_ROOT_USER", "").strip()
        secret_key = os.getenv("MINIO_ROOT_PASSWORD", "").strip()
        bucket = os.getenv("S3_BUCKET", os.getenv("MINIO_BUCKET", "")).strip()
        model_key = os.getenv("S3_MODEL_KEY", "model.keras").strip()
        classes_key = os.getenv("S3_CLASSES_KEY", "classes.txt").strip()

        if not all((endpoint_url, access_key, secret_key, bucket)):
            return None

        return cls(
            endpoint_url=endpoint_url,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket,
            model_key=model_key,
            classes_key=classes_key,
        )

    def _build_client(self) -> Any:
        """Instancia um cliente boto3 para o endpoint S3 informado."""
        try:
            import boto3
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Dependência 'boto3' não encontrada. Instale para usar download via S3."
            ) from exc

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="us-east-1",
        )

    def _download_file(
        self,
        client: Any,
        object_key: str,
        destination: Path,
        overwrite: bool,
    ) -> Path:
        """Baixa um arquivo do bucket para o caminho local informado."""
        if destination.exists() and not overwrite:
            logger.info(
                "Artefato já existe localmente; download ignorado | path=%s", destination
            )
            return destination

        destination.parent.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Download iniciado | bucket=%s key=%s destino=%s endpoint=%s",
            self.bucket,
            object_key,
            destination,
            self.endpoint_url,
        )
        client.download_file(
            Bucket=self.bucket,
            Key=object_key,
            Filename=str(destination),
        )
        logger.info("Download concluído | path=%s", destination)
        return destination

    def download_model_and_classes(
        self,
        model_dest: str | Path,
        classes_dest: str | Path,
        overwrite: bool = False,
    ) -> tuple[Path, Path]:
        """Baixa `model.keras` e `classes.txt` para caminhos locais."""
        client = self._build_client()

        model_path = self._download_file(
            client=client,
            object_key=self.model_key,
            destination=Path(model_dest),
            overwrite=overwrite,
        )
        classes_path = self._download_file(
            client=client,
            object_key=self.classes_key,
            destination=Path(classes_dest),
            overwrite=overwrite,
        )
        return model_path, classes_path


def download_inference_artifacts_from_env(
    model_dest: str | Path,
    classes_dest: str | Path,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Baixa artefatos de inferência exigindo configuração S3 válida."""
    downloader = S3ArtifactsDownloader.from_env()
    if downloader is None:
        raise RuntimeError(
            "Configuração S3 incompleta. Defina MINIO_URL, MINIO_ROOT_USER, "
            "MINIO_ROOT_PASSWORD e S3_BUCKET (ou MINIO_BUCKET)."
        )

    return downloader.download_model_and_classes(
        model_dest=model_dest,
        classes_dest=classes_dest,
        overwrite=overwrite,
    )
