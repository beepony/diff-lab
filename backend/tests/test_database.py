def test_database_uses_migrations_and_sqlite_integrity_pragmas(client):
    from db import engine

    with engine.connect() as connection:
        version = connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
        foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
        journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar_one()
        indexes = connection.exec_driver_sql("PRAGMA index_list('share_links')").mappings().all()

    assert version == "0001_initial_schema"
    assert foreign_keys == 1
    assert journal_mode == "wal"
    assert any(index["name"] == "ix_share_links_access_token" and index["unique"] == 1 for index in indexes)
