"""
Database router for the verion-ai-grader service.

Two database connections:
  default  — SQLite (local file). Holds Django system tables and auth_keys.
             Never touches the shared Neon database.
  neon     — Shared PostgreSQL (Neon). Holds grader app tables only.
             All managed=False models (main system tables) are also read/written
             here, but Django never runs CREATE/ALTER/DROP against them.

Routing rules:
  grader app      → neon
  everything else → default  (auth_keys, contenttypes, auth, django internals)
"""

NEON_APPS = {'grader'}


class GraderRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label in NEON_APPS:
            return 'neon'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in NEON_APPS:
            return 'neon'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations within the same database
        db1 = 'neon' if obj1._meta.app_label in NEON_APPS else 'default'
        db2 = 'neon' if obj2._meta.app_label in NEON_APPS else 'default'
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in NEON_APPS:
            # grader migrations run on neon only
            return db == 'neon'
        # Everything else (auth_keys, contenttypes, auth, django internals)
        # migrates on default (SQLite) only
        return db == 'default'
