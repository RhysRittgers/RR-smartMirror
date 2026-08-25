import os
import asyncio

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "smart_mirror_project.settings"
)

import django
django.setup()

from Stocks.alert_monitor import monitor_stock_alerts


if __name__ == "__main__":
    asyncio.run(
        monitor_stock_alerts()
    )