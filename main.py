import logging

import uvicorn

from seo_scanner_service.api import app
from seo_scanner_service.settings import settings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=settings.app.port, log_level="info")  # noqa: S104
