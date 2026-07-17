# Vercel Database Compatibility & Configuration
# CTF Arena v1.0.0 — EthicBids Technologies™

This document outlines PostgreSQL database compatibility requirements for serverless deployments on Vercel.

---

## 1. Remote Database Requirements

Because Vercel functions are stateless and spin down between requests, a local SQLite database file cannot be used. A remote PostgreSQL database (such as Supabase, Neon, or AWS RDS) is required.

---

## 2. SSL/TLS Connection Configuration

To secure credentials and database payloads in transit, all connections from Vercel to the remote PostgreSQL database must enforce TLS encryption.

- **Append parameters**: Add `?sslmode=require` or `?ssl=true` to the `DATABASE_URL` string inside Vercel Dashboard.
- **Example connection URL**:
  `postgresql://ctf_user:password@host.provider.com:5432/ctf_db?sslmode=require`

---

## 3. Serverless Connection Pooling

Serverless lambdas can scale horizontally up to hundreds of concurrent instances. Each instance opens a new connection to the database, which can quickly exhaust the PostgreSQL maximum connection limit (`max_connections`).

- **SQLAlchemy Pool Recycle**: Set pool recycling parameters to automatically drop idle connections.
- **PgBouncer / Connection Pooler**: It is highly recommended to route connection URLs through a pooler (like PgBouncer or Neon connection pool port `5432` with transaction pooling enabled).
