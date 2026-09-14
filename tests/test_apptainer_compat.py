from utils import apptainer_compat


def test_dockerfile_post_exec_uses_fakeroot_when_enabled(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(apptainer_compat, "USE_FAKEROOT_BUILD", True)
    sandbox = tmp_path / "rootfs"

    args = apptainer_compat._dockerfile_post_exec_args(sandbox)

    assert args == [
        "exec",
        "--fakeroot",
        "--writable",
        str(sandbox),
        "bash",
        "/dockerfile-post.sh",
    ]


def test_dockerfile_post_exec_can_disable_fakeroot(monkeypatch, tmp_path):
    monkeypatch.setattr(apptainer_compat, "USE_FAKEROOT_BUILD", False)
    sandbox = tmp_path / "rootfs"

    args = apptainer_compat._dockerfile_post_exec_args(sandbox)

    assert args == [
        "exec",
        "--writable",
        str(sandbox),
        "bash",
        "/dockerfile-post.sh",
    ]
