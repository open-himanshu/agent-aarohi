from aarohi.cli import main


def test_about_command(capsys):
    main([])
    captured = capsys.readouterr()
    assert "Aarohi" in captured.out
    assert "personal AI agent" in captured.out
