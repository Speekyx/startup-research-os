"""Worker entrypoint.

    celery -A sros_workers.worker_entry:app worker -Q acquisition,nlp,embedding,analysis,maintenance

Probe tasks are registered only when SROS_ENABLE_PROBE_TASKS=1, so an
infrastructure probe cannot reach a production worker by accident.
"""

from __future__ import annotations

import os

from .celery_app import create_celery_app

app = create_celery_app()

if os.environ.get("SROS_ENABLE_PROBE_TASKS") == "1":
    from .probe import register_probe_tasks

    register_probe_tasks(app)
