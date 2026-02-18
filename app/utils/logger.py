"""Utilitários para configurar logs da aplicação com rotação de arquivos."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from logging.handlers import RotatingFileHandler


@dataclass
class LoggerConfig:
    """Configura e expõe uma instância reutilizável de logger da aplicação."""

    name: str = "app_logger"
    log_dir: str = "logs"
    log_file: str = "app.log"
    max_mbytes: int = 5
    num_files: int = 5
    logger: logging.Logger = field(init=False, repr=False)
    _log_dir_path: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Configura o logger após a inicialização automática da dataclass."""
        self._log_dir_path = Path(self.log_dir)
        self.logger = self._configure_logger()

    def _configure_logger(self) -> logging.Logger:
        """Cria e configura os handlers do logger quando necessário."""
        self._log_dir_path.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        if logger.handlers:
            return logger

        formatter = self._create_formatter()
        logger.addHandler(self._create_file_handler(formatter))
        logger.addHandler(self._create_console_handler(formatter))
        return logger

    @staticmethod
    def _create_formatter() -> logging.Formatter:
        """Cria o formatador padrão para os logs."""
        return logging.Formatter(
            fmt="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _create_file_handler(self, formatter: logging.Formatter) -> RotatingFileHandler:
        """Cria o handler de arquivo com rotação."""
        file_handler = RotatingFileHandler(
            filename=self._log_dir_path / self.log_file,
            maxBytes=self.max_mbytes * 1024 * 1024,
            backupCount=self.num_files,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        return file_handler

    @staticmethod
    def _create_console_handler(
        formatter: logging.Formatter,
    ) -> logging.StreamHandler:
        """Cria o handler de console."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        return console_handler

    def get_logger(self) -> logging.Logger:
        """Retorna a instância de logger configurada."""
        return self.logger
