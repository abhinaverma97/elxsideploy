#!/usr/bin/env python3
"""Check rag_documents count in the configured DATABASE_URL."""
import os
from sqlalchemy import create_engine, text
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

# Load .env if available so DATABASE_URL from .env is picked up
if load_dotenv:
    try:
        load_dotenv()
    except Exception:
        pass

def main():
    url = os.environ.get('DATABASE_URL')
    print('DATABASE_URL=', url)
    if not url:
        print('DATABASE_URL not set in environment; please ensure .env is loaded or set the var.')
        return 2
    eng = create_engine(url)
    with eng.connect() as conn:
        try:
            r = conn.execute(text('select count(*) from rag_documents'))
            print('rag_documents count =', r.scalar())
            return 0
        except Exception as e:
            print('error querying rag_documents:', e)
            return 3

if __name__ == '__main__':
    raise SystemExit(main())
