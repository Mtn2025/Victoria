# Rollback Procedures

## 1. Automated Rollback (GitHub Actions)
If the deployment workflow fails during the process, the pipeline is designed to stop. However, if a bad build is deployed successfully:

1. Identification:
   - Monitor alerts in `#ops-alerts` or Sentry.
   - Verify health check failures.

2. Revert:
   - Go to GitHub Actions tab.
   - Select the last successful workflow run.
   - Click "Re-run jobs".
   - Alternatively, revert the merge commit in `main` branch: `git revert HEAD`.

## 2. Manual Docker Rollback
If GitHub Actions is unavailable, SSH into the server:

```bash
# 1. Identify previous tag
docker images | grep victoria-backend

# 2. Update .env or docker-compose to point to previous tag
# VERSION=v1.0.0 -> VERSION=v0.9.9

# 3. Redeploy
docker-compose -f docker-compose.prod.yml up -d
```

## 3. Database Rollback
If a migration caused data corruption or schema issues:

```bash
# Downgrade to previous revision
alembic downgrade -1
```

*Warning: Data migration rollbacks can be destructive. Always backup before downgrading.*
