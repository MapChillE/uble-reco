import redis
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

ssl_cert_map = {
    "none": ssl.CERT_NONE,
    "required": ssl.CERT_REQUIRED,
    "optional": ssl.CERT_OPTIONAL
}

r = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    ssl=True,
    ssl_cert_reqs=ssl_cert_map[os.getenv("REDIS_SSL_CERT_REQS", "required").lower()],
    decode_responses=True
)
