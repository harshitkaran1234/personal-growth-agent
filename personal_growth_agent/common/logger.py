import logging

import ecs_logging

logger = logging.getLogger("personal_growth_agent")

logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(ecs_logging.StdlibFormatter())
logger.addHandler(handler)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
