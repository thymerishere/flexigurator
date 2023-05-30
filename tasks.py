from invoke.tasks import task
from invoke.terminals import WINDOWS


_PROJ_PATH = "flexigurator"
# If you use Windows you do not get shiny colours
_PTY_AVAILABLE = not WINDOWS


@task
def apply_formatting(context):
    """Apply black."""
    context.run(f"isort --profile black {_PROJ_PATH}", pty=_PTY_AVAILABLE)
    context.run(f"black {_PROJ_PATH} --line-length=100", pty=_PTY_AVAILABLE)


@task
def formatting(context):
    """Run black but only show the diff."""
    context.run(f"isort --check --profile black {_PROJ_PATH}", pty=_PTY_AVAILABLE)
    context.run(
        f"black {_PROJ_PATH} --line-length=100 --diff --color", pty=_PTY_AVAILABLE
    )


@task
def types(context):
    """Use MyPy to check whether types are correctly used."""
    context.run(f"mypy {_PROJ_PATH}", pty=_PTY_AVAILABLE)


@task
def complexity(context):
    """Use Radon and Xenon to test code complexity."""
    # Radon to view code complexity
    context.run(
        f"radon cc {_PROJ_PATH} --total-average --show-complexity",
        pty=_PTY_AVAILABLE,
    )
    # Xenon to enforce code complexity
    context.run(
        f"xenon {_PROJ_PATH} --max-absolute B --max-modules B --max-average A",
        pty=_PTY_AVAILABLE,
    )


def docstyle(context):
    """Use darglint to check documentation style according to Google guidelines."""
    context.run(f"darglint {_PROJ_PATH} -v 2", pty=_PTY_AVAILABLE)

@task
def test(context, is_local=False):
    """Use Pytest to run all tests."""
    context.run(f"pytest --cov={_PROJ_PATH} {'--cov-report term --cov-report html' if is_local else ''} tests", pty=_PTY_AVAILABLE)


@task
def local(context):
    """Run a local pipeline which also applies formatting tools.

    Make sure to check for unstaged changes after running a local pipeline.
    """
    apply_formatting(context)
    pipeline(context, is_local=True)


@task
def pipeline(context, is_local=False):
    """Run the full quality and testing pipeline."""
    types(context)
    complexity(context)
    formatting(context)
    docstyle(context)
    test(context, is_local)
