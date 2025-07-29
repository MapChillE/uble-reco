import os
import logging
import logging.config
import yaml

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.traceId = getattr(record, 'traceId', '-')
        record.endpoint = getattr(record, 'endpoint', '-')
        record.status = getattr(record, 'status', '-')
        record.latencyMs = getattr(record, 'latencyMs', '-')
        record.userId = getattr(record, 'userId', '-')
        return True

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    path = "logging_config.yaml"
    if os.path.exists(path):
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger().addFilter(ContextFilter())