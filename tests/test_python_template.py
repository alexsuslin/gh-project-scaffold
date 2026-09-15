import os
import subprocess
import sys
import venv

from copier import run_copy


def run(*command, cwd):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def test_python_template_builds_and_installs_without_source_checkout(tmp_path, template_source):
    project = tmp_path / "sample project"
    run_copy(
        str(template_source),
        project,
        data={"project_name": "sample-project", "owner": "example"},
        vcs_ref="v1.0.0",
        defaults=True,
        quiet=True,
        skip_tasks=True,
    )
    run(sys.executable, "-m", "ruff", "format", "--check", ".", cwd=project)
    run(sys.executable, "-m", "ruff", "check", ".", cwd=project)
    run(sys.executable, "-m", "build", "--no-isolation", cwd=project)
    wheels = list((project / "dist").glob("*.whl"))
    assert len(wheels) == 1
    assert len(list((project / "dist").glob("*.tar.gz"))) == 1

    # A clean environment catches wheels that accidentally omit the src package.
    environment = tmp_path / "installed"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    run(
        str(python),
        "-m",
        "pip",
        "install",
        "--no-index",
        "--no-deps",
        str(wheels[0]),
        cwd=tmp_path,
    )
    run(
        str(python),
        "-I",
        "-c",
        "import sample_project; from importlib.metadata import version; "
        "assert version('sample-project') == '0.1.0'",
        cwd=tmp_path,
    )
