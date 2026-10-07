#!/usr/bin/env python
"""
Management CLI script for running server and tests.
"""
import sys
import uvicorn
import pytest


def main():
    args = sys.argv[1:]
    command = args[0] if args else "help"

    if command == "runserver":
        port = 8000
        host = "127.0.0.1"
        
        # Parse optional port or host:port argument (e.g., manage.py runserver 8000)
        if len(args) > 1:
            val = args[1]
            if ":" in val:
                h, p = val.split(":", 1)
                if h:
                    host = h
                if p.isdigit():
                    port = int(p)
            elif val.isdigit():
                port = int(val)

        print(f"\n🚀 Starting Bulk Certificate API server on http://{host}:{port}")
        print(f"📖 Interactive OpenAPI Docs: http://{host}:{port}/docs\n")
        
        uvicorn.run("app.main:app", host=host, port=port, reload=True)

    elif command == "test":
        print("\n🧪 Running pytest test suite...\n")
        sys.exit(pytest.main(["-v"] + args[1:]))

    else:
        print("\nUsage:")
        print("  python manage.py runserver [port or host:port]")
        print("  python manage.py test\n")


if __name__ == "__main__":
    main()
