from aarohi.cli import main
from aarohi.database import connect, initialise


def test_database_check_and_backup_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    initialise(tmp_path / "storage" / "aarohi.db")

    assert main(["db", "check"]) == 0
    assert '"healthy": true' in capsys.readouterr().out

    backup = tmp_path / "private-backup" / "aarohi-copy.db"
    assert main(["db", "backup", str(backup)]) == 0
    assert "Database backup created" in capsys.readouterr().out
    assert backup.is_file()


def test_database_restore_cli_requires_explicit_overwrite(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AAROHI_HOME", str(tmp_path))
    database = tmp_path / "storage" / "aarohi.db"
    initialise(database)
    db = connect(database)
    db.execute("INSERT INTO tasks VALUES ('task-1', 'Before backup', 'planned', 't0', 't0')")
    db.commit()
    db.close()

    backup = tmp_path / "safe-backup.db"
    assert main(["db", "backup", str(backup)]) == 0
    capsys.readouterr()

    db = connect(database)
    db.execute("UPDATE tasks SET goal='Changed after backup' WHERE id='task-1'")
    db.commit()
    db.close()

    assert main(["db", "restore", str(backup)]) == 2
    assert "with --yes" in capsys.readouterr().err

    assert main(["db", "restore", str(backup), "--yes"]) == 0
    assert "Database restored" in capsys.readouterr().out

    db = connect(database)
    assert db.execute("SELECT goal FROM tasks WHERE id='task-1'").fetchone()[0] == "Before backup"
    db.close()
