# API Reference

## Authentication
- `POST /api/auth/register` — Register a new user
- `POST /api/auth/login` — Login and receive JWT token
- `GET /api/auth/me` — Get current user info
- `POST /api/auth/forgot-password` — Request a password reset link
- `POST /api/auth/reset-password` — Complete password reset with reset token
- `POST|PATCH|PUT /api/auth/change-password` — Change password while logged in
- `GET /api/auth/verify-email?token=...` — Verify email using a signed token

## Users
- `GET /api/users/` — List all users
- `GET /api/users/{id}` — Get user by ID
- `PATCH /api/users/{id}` — Update user
- `DELETE /api/users/{id}` — Delete user

## Feedback
- `POST /api/feedback/` — Submit feedback
- `GET /api/feedback/mine` — Get my feedback
- `GET /api/feedback/` — Get all feedback (admin)

## RAG Search
- `POST /api/rag/search` — Search documents
- `POST /api/rag/upload-pdf` — Upload PDF
- `GET /api/rag/pdfs` — List PDFs
- `DELETE /api/rag/pdfs/{id}` — Delete PDF
- `POST /api/rag/pdfs/{id}/index` — Index PDF
- `GET /api/rag/pdfs/{id}` — Get PDF details
- `GET /api/rag/search-history` — Get search history
- `GET /api/rag/trending` — Get trending topics

## Analytics
- `GET /api/analytics/summary` — System summary
- `GET /api/analytics/usage-by-role` — Usage by role
- `GET /api/analytics/feedback-sentiment` — Student feedback sentiment breakdown

_See the codebase for request/response examples._
