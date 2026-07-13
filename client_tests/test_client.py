# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = REPO_ROOT / "client_tests" / "app"
DEPENDENCY_ID = "anvil_reactive_under_test"
RESULT_SELECTOR = "#anvil-reactive-test-result[data-state=done]"
PAGE_TIMEOUT_MS = 30_000


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(origin, process, log_path, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(
                "Anvil App Server exited before becoming ready:\n"
                + log_path.read_text(errors="replace")
            )
        try:
            with urllib.request.urlopen(origin, timeout=1) as response:
                if response.status < 500:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    pytest.fail(
        f"Anvil App Server did not become ready within {timeout}s:\n"
        + log_path.read_text(errors="replace")
    )


def _wait_for_postgres(container_name, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready = subprocess.run(
            ["docker", "exec", container_name, "pg_isready", "-U", "postgres"],
            capture_output=True,
            text=True,
        )
        if ready.returncode == 0:
            return
        time.sleep(0.25)
    logs = subprocess.run(
        ["docker", "logs", container_name], capture_output=True, text=True
    )
    pytest.fail(f"Postgres container did not become ready:\n{logs.stdout}{logs.stderr}")


@contextmanager
def _database_url():
    configured = os.getenv("ANVIL_REACTIVE_TEST_DATABASE")
    if configured:
        yield configured
        return

    needs_external_database = (
        platform.system() == "Darwin" and platform.machine() == "arm64"
    )
    if not needs_external_database:
        yield None
        return

    if shutil.which("docker") is None:
        pytest.skip(
            "The bundled App Server database does not support Apple Silicon and "
            "Docker is unavailable"
        )

    port = _free_port()
    container_name = f"anvil-reactive-tests-{uuid4().hex[:12]}"
    run = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--detach",
            "--name",
            container_name,
            "--env",
            "POSTGRES_PASSWORD=postgres",
            "--env",
            "POSTGRES_DB=anvil_reactive_tests",
            "--publish",
            f"127.0.0.1:{port}:5432",
            "postgres:16-alpine",
        ],
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        pytest.fail(f"Could not start Postgres container:\n{run.stdout}{run.stderr}")
    try:
        _wait_for_postgres(container_name)
        yield (
            f"jdbc:postgresql://127.0.0.1:{port}/anvil_reactive_tests"
            "?user=postgres&password=postgres"
        )
    finally:
        subprocess.run(["docker", "rm", "--force", container_name], capture_output=True)


@contextmanager
def _app_server(tmp_path):
    executable = shutil.which("anvil-app-server")
    if executable is None:
        venv_executable = Path(sys.executable).with_name("anvil-app-server")
        if venv_executable.exists():
            executable = str(venv_executable)
    if executable is None:
        pytest.skip("anvil-app-server is not installed")

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    app_path = workspace / "client_test_app"
    dependency_path = workspace / "anvil_reactive"
    app_path.symlink_to(APP_SOURCE, target_is_directory=True)
    dependency_path.symlink_to(REPO_ROOT, target_is_directory=True)

    data_path = tmp_path / "app-server-data"
    data_path.mkdir()
    log_path = tmp_path / "app-server.log"
    port = _free_port()
    origin = f"http://127.0.0.1:{port}"
    command = [
        executable,
        "--app",
        str(app_path),
        "--dep-id",
        f"{DEPENDENCY_ID}=anvil_reactive",
        "--data-dir",
        str(data_path),
        "--origin",
        origin,
        "--port",
        str(port),
    ]

    with _database_url() as database_url:
        if database_url:
            command.extend(["--database", database_url])

        with log_path.open("w") as log:
            process = subprocess.Popen(
                command,
                cwd=workspace,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                _wait_until_ready(origin, process, log_path)
                yield origin, log_path
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)


def _load_client_page(browser, url, tmp_path, log_path, label):
    console = []
    failed_requests = []
    page = browser.new_page()
    page.on(
        "console",
        lambda message: console.append(f"{message.type}: {message.text}"),
    )
    page.on(
        "requestfailed",
        lambda request: failed_requests.append(f"{request.url}: {request.failure}"),
    )
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
        page.locator(RESULT_SELECTOR).wait_for(timeout=PAGE_TIMEOUT_MS)
        payload = json.loads(page.locator(RESULT_SELECTOR).text_content())
        failed = payload["status"] == "fail"
    except Exception as error:
        payload = None
        failed = True
        load_error = f"{type(error).__name__}: {error}"
    else:
        load_error = None

    diagnostics = None
    if failed:
        screenshot = tmp_path / f"client-test-{label}.png"
        html = tmp_path / f"client-test-{label}.html"
        page.screenshot(path=str(screenshot), full_page=True)
        html.write_text(page.content())
        diagnostics = (
            f"Client page {label!r} failed.\n\n"
            f"Load error: {load_error or 'None'}\n\n"
            f"Payload:\n{json.dumps(payload, indent=2) if payload else 'None'}\n\n"
            f"App Server log:\n{log_path.read_text(errors='replace')}\n\n"
            f"Console:\n{chr(10).join(console) or 'None'}\n\n"
            f"Failed requests:\n{chr(10).join(failed_requests) or 'None'}\n\n"
            f"Page HTML: {html}\nScreenshot: {screenshot}"
        )
    page.close()
    return payload, diagnostics


def test_reactive_dependency_in_real_client(tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")

    diagnostics = []
    with _app_server(tmp_path) as (origin, log_path):
        with playwright.sync_playwright() as runtime:
            browser = runtime.chromium.launch(headless=True)
            discovery, failure = _load_client_page(
                browser,
                f"{origin}/?discover=1",
                tmp_path,
                log_path,
                "discovery",
            )
            if failure:
                diagnostics.append(failure)
            assert discovery is not None, "\n\n".join(diagnostics)
            assert discovery["status"] == "discovered"

            suite, failure = _load_client_page(
                browser, origin, tmp_path, log_path, "shared-suite"
            )
            if failure:
                diagnostics.append(failure)
            results = list(suite["cases"]) if suite is not None else []

            for metadata in discovery["cases"]:
                if not metadata["fresh_page"]:
                    continue
                name = metadata["name"]
                encoded_name = urllib.parse.quote(name, safe="")
                payload, failure = _load_client_page(
                    browser,
                    f"{origin}/?case={encoded_name}",
                    tmp_path,
                    log_path,
                    name,
                )
                if failure:
                    diagnostics.append(failure)
                if payload is not None:
                    assert len(payload["cases"]) == 1
                    assert payload["cases"][0]["name"] == name
                    results.extend(payload["cases"])
            browser.close()

        server_log = log_path.read_text(errors="replace")

    assert "Tried to read a disposed computation" not in server_log
    discovered_names = [case["name"] for case in discovery["cases"]]
    assert len(discovered_names) == len(set(discovered_names))
    assert {case["name"] for case in results} == set(discovered_names)

    failures = [case for case in results if case["status"] in ("fail", "xpass")]
    assert not failures, "\n\n".join([json.dumps(failures, indent=2), *diagnostics])

    cases = {case["name"]: case for case in results}
    expected_component_cases = {
        "render_effect_waits_for_mount",
        "hidden_render_effect_remains_active",
        "removed_render_effect_pauses_and_restarts",
        "component_effect_matches_render_effect_lifecycle",
        "bind_lambda_syncs_across_lifecycle",
        "bind_object_attribute_syncs",
        "bind_dict_key_syncs",
        "writeback_object_attribute_updates_both_directions",
        "writeback_callable_accepts_multiple_events",
        "writeback_updates_source_before_later_event_handlers",
        "writeback_does_not_duplicate_handlers_after_remount",
        "unmounted_writeback_event_is_ignored",
    }
    assert expected_component_cases <= cases.keys()
    expected_datatable_cases = {
        "datatable_model_preserves_surface_and_linked_values",
        "buffered_model_save_and_reset",
        "server_round_trip_refreshes_same_model",
        "server_round_trip_preserves_python_identity",
        "reactive_instance_does_not_mutate_model_class",
        "reactive_model_attribute_updates_effect",
        "reactive_model_property_updates_effect",
        "reactive_model_item_updates_effect",
        "reactive_model_link_replacement_updates_effect",
        "server_model_update_notifies_effect",
    }
    assert expected_datatable_cases <= cases.keys()
    assert cases["suspending_case_is_awaited"]["status"] == "pass"
    assert cases["multiple_sequential_suspensions_resume_in_order"]["status"] == (
        "pass"
    )
    assert cases["post_suspension_exception_reaches_the_caller"]["status"] == "pass"
    assert cases["only_reads_before_first_suspension_are_tracked"]["status"] == ("pass")
    isolated_cases = {case["name"] for case in discovery["cases"] if case["fresh_page"]}
    assert {
        "multiple_sequential_suspensions_resume_in_order",
        "only_reads_before_first_suspension_are_tracked",
        "post_suspension_exception_reaches_the_caller",
    } <= isolated_cases
    assert cases["reset_discards_queued_effects"]["status"] == "pass"
    traceback_case = cases["skulpt_traceback_is_reported"]
    assert traceback_case["status"] == "pass"
    assert "traceback_probe" in traceback_case["traceback"]
    known_gap = cases["unmounted_writeback_event_is_ignored"]
    assert known_gap["classification"] == "known_gap"
    assert known_gap["status"] == "xfail"
    assert {case["name"] for case in cases.values() if case["status"] == "xfail"} == {
        "component_effect_matches_render_effect_lifecycle",
        "dependency_change_while_first_execution_is_pending",
        "disposal_invalidates_pending_completion",
        "newer_async_execution_supersedes_older_result",
        "pending_work_preserves_dependency_reconciliation",
        "reactive_instance_does_not_mutate_model_class",
        "server_round_trip_preserves_python_identity",
        "unmounted_writeback_event_is_ignored",
    }
    for case in cases.values():
        assert case["status"] in ("pass", "xfail")
        assert case["duration_ms"] >= 0
