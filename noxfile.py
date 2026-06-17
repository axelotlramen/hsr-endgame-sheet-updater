import nox


@nox.session
def reformat(session):
    session.install("ruff", "black")

    session.run("ruff", "check", "--fix", ".")
    session.run("black", ".")
