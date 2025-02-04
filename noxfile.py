""" nox conf file for running tasks on multiple pythons """

import nox


@nox.session(python=["3.12"])
def tests(session):
    """run tests"""
    session.install("poetry")
    session.run("poetry", "install")
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "report")


@nox.session
def lint(session):
    """run linter"""
    session.install("poetry")
    session.run("poetry", "install")
    session.run("black", "--check", ".")
    session.run("flake8", ".")


@nox.session
def typing(session):
    """static type check"""
    session.install("poetry")
    session.run("poetry", "install")
    session.run("mypy", ".")
