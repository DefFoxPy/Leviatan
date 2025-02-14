import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

def setup_logging():
    # Crear directorio de logs si no existe
    log_dir = "Data/Logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configurar logger principal
    logger = logging.getLogger('tamagotchi_democrata')
    logger.setLevel(logging.INFO)

    # Handler para errores críticos
    error_handler = RotatingFileHandler(
        f"{log_dir}/errors.log",
        maxBytes=1024*1024,  # 1MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(module)s:%(lineno)d - %(message)s'
    )
    error_handler.setFormatter(error_formatter)

    # Handler para eventos del sistema
    system_handler = RotatingFileHandler(
        f"{log_dir}/system.log",
        maxBytes=1024*1024,
        backupCount=5
    )
    system_handler.setLevel(logging.INFO)
    system_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(module)s - %(message)s'
    )
    system_handler.setFormatter(system_formatter)

    # Handler para votaciones
    voting_handler = RotatingFileHandler(
        f"{log_dir}/voting.log",
        maxBytes=1024*1024,
        backupCount=5
    )
    voting_handler.setLevel(logging.INFO)
    voting_formatter = logging.Formatter(
        '%(asctime)s [VOTE] %(message)s'
    )
    voting_handler.setFormatter(voting_formatter)

    # Añadir handlers al logger
    logger.addHandler(error_handler)
    logger.addHandler(system_handler)
    logger.addHandler(voting_handler)

    return logger

# Crear loggers específicos
error_logger = logging.getLogger('tamagotchi_democrata.errors')
system_logger = logging.getLogger('tamagotchi_democrata.system')
voting_logger = logging.getLogger('tamagotchi_democrata.voting')

def log_error(error: Exception, context: str = None):
    """Log errores con contexto"""
    error_logger.error(
        f"Error: {str(error)}\n" + 
        f"Context: {context}\n" +
        f"Type: {type(error).__name__}"
    )

def log_vote(proposal_id: str, voter_id: str, action: str, details: dict):
    """Log eventos de votación"""
    voting_logger.info(
        f"Proposal: {proposal_id} | " +
        f"Voter: {voter_id} | " +
        f"Action: {action} | " +
        f"Details: {details}"
    )

def log_system_event(event: str, details: dict = None):
    """Log eventos del sistema"""
    system_logger.info(
        f"Event: {event}\n" +
        f"Details: {details if details else 'No details provided'}"
    )
