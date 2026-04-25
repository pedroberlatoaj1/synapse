#!/usr/bin/env python
"""Django management entrypoint for the Synapse API."""
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "synapse.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and the "
            "virtualenv is activated (see `make api-install`)."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
