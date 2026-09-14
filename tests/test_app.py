from __future__ import annotations

from io import StringIO
from unittest.mock import Mock, call

import pytest

from vanta.app import Console, DEFAULT_NO, DEFAULT_YES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeStream(StringIO):
    def __init__(self, *, tty: bool = False) -> None:
        super().__init__()
        self.tty = tty

    def isatty(self) -> bool:
        return self.tty


# ---------------------------------------------------------------------------
# Construction / color detection
# ---------------------------------------------------------------------------


def test_color_is_disabled_for_non_tty_by_default() -> None:
    stream = FakeStream(tty=False)

    console = Console(cls=False, stream=stream)

    assert console._color is False


def test_color_is_enabled_for_tty_by_default() -> None:
    stream = FakeStream(tty=True)

    console = Console(cls=False, stream=stream)

    assert console._color is True


def test_color_false_disables_color_even_on_tty() -> None:
    stream = FakeStream(tty=True)

    console = Console(color=False, cls=False, stream=stream)

    assert console._color is False


def test_color_true_does_not_force_ansi_into_non_tty() -> None:
    stream = FakeStream(tty=False)

    console = Console(color=True, cls=False, stream=stream)

    assert console._color is False


def test_invalid_tty_stream_is_treated_as_non_tty() -> None:
    stream = Mock()
    stream.isatty.side_effect = OSError

    console = Console(cls=False, stream=stream)

    assert console._color is False


# ---------------------------------------------------------------------------
# Prefixes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "variant",
    [
        "success",
        "info",
        "warning",
        "error",
        "notice",
    ],
)
def test_prefix_contains_variant_name(variant: str) -> None:
    console = Console(color=False, cls=False)

    prefix = console._prefix(variant)

    assert prefix == f"[{variant.upper()}] "


def test_prefix_falls_back_to_info_for_unknown_variant() -> None:
    console = Console(color=False, cls=False)

    assert console._prefix("does-not-exist") == "[INFO] "


def test_prefix_is_case_insensitive() -> None:
    console = Console(color=False, cls=False)

    assert console._prefix("SUCCESS") == "[SUCCESS] "


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method, variant",
    [
        ("info", "INFO"),
        ("success", "SUCCESS"),
        ("warning", "WARNING"),
        ("error", "ERROR"),
        ("notice", "NOTICE"),
    ],
)
def test_message_methods_write_expected_variant(
    method: str,
    variant: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = FakeStream()

    console = Console(color=False, cls=False, stream=stream)

    monkeypatch.setattr(console, "_timestamp", lambda: "12:34:56")

    getattr(console, method)("hello")

    assert stream.getvalue() == f"[12:34:56] [{variant}] hello\n"


def test_raw_with_timestamp() -> None:
    stream = FakeStream()

    console = Console(color=False, cls=False, stream=stream)

    console._timestamp = lambda: "12:34:56"

    console.raw("hello")

    assert stream.getvalue() == "[12:34:56] hello\n"


def test_raw_without_timestamp() -> None:
    stream = FakeStream()

    console = Console(color=False, cls=False, stream=stream)

    console.raw("hello", timestamp=False)

    assert stream.getvalue() == "hello\n"


# ---------------------------------------------------------------------------
# ask()
# ---------------------------------------------------------------------------


def test_ask_returns_converted_value(monkeypatch: pytest.MonkeyPatch) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "123")

    result = console.ask("Number:", int)

    assert result == 123


def test_ask_retries_after_invalid_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    answers = iter(["abc", "42"])

    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = console.ask("Number:", int)

    assert result == 42


def test_ask_respects_retry_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "abc")

    with pytest.raises(ValueError, match="Maximum number of retries"):
        console.ask("Number:", int, retry=3)


def test_ask_retry_zero_means_infinite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    answers = iter(["bad", "bad", "42"])

    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    result = console.ask("Number:", int, retry=0)

    assert result == 42


def test_ask_custom_error_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "bad")

    # Keep the test finite.
    with pytest.raises(ValueError):
        console.ask(
            "Number:",
            int,
            error_message="Not a number.",
            retry=1,
        )

    output = capsys.readouterr().out

    assert "Not a number." in output


def test_ask_handles_eof(monkeypatch: pytest.MonkeyPatch) -> None:
    console = Console(color=False, cls=False)

    def raise_eof(_: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    with pytest.raises(EOFError):
        console.ask("Input:")


def test_ask_handles_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    def raise_interrupt(_: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)

    with pytest.raises(KeyboardInterrupt):
        console.ask("Input:")


# ---------------------------------------------------------------------------
# confirm()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "answer, expected",
    [
        ("y", True),
        ("Y", True),
        ("yes", True),
        ("YES", True),
        ("1", True),
        ("ok", True),
        ("ye", True),
        ("yep", True),
        ("yy", True),
        ("n", False),
        ("N", False),
        ("no", False),
        ("0", False),
        ("nah", False),
        ("nn", False),
    ],
)
def test_confirm_default_aliases(
    monkeypatch: pytest.MonkeyPatch,
    answer: str,
    expected: bool,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: answer)

    assert console.confirm("Continue?") is expected


def test_confirm_default_true(monkeypatch: pytest.MonkeyPatch) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "")

    assert console.confirm("Continue?", default=True) is True


def test_confirm_default_false(monkeypatch: pytest.MonkeyPatch) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "")

    assert console.confirm("Continue?", default=False) is False


def test_confirm_custom_yes_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "yeah")

    assert console.confirm(
        "Continue?",
        alias_yes=["yeah"],
    ) is True


def test_confirm_custom_no_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "nope")

    assert console.confirm(
        "Continue?",
        alias_no=["nope"],
    ) is False


def test_confirm_aliases_are_case_insensitive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "YUH")

    assert console.confirm(
        "Continue?",
        alias_yes=["yuh"],
    ) is True


def test_confirm_aliases_ignore_empty_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "yeah")

    assert console.confirm(
        "Continue?",
        alias_yes=["", "  ", "yeah"],
    ) is True


def test_confirm_retries_invalid_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    answers = iter(["maybe", "yes"])

    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert console.confirm("Continue?") is True


def test_confirm_respects_retry_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "maybe")

    with pytest.raises(ValueError, match="Maximum number of retries"):
        console.confirm("Continue?", retry=3)


def test_confirm_retry_zero_means_infinite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    answers = iter(["maybe", "wat", "yes"])

    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert console.confirm("Continue?", retry=0) is True


def test_confirm_custom_error_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr("builtins.input", lambda _: "maybe")

    with pytest.raises(ValueError):
        console.confirm(
            "Continue?",
            error_message="Please enter Y or N.",
            retry=1,
        )

    assert "Please enter Y or N." in capsys.readouterr().out


def test_confirm_handles_eof(monkeypatch: pytest.MonkeyPatch) -> None:
    console = Console(color=False, cls=False)

    def raise_eof(_: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    with pytest.raises(EOFError):
        console.confirm("Continue?")


def test_confirm_handles_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    def raise_interrupt(_: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)

    with pytest.raises(KeyboardInterrupt):
        console.confirm("Continue?")


# ---------------------------------------------------------------------------
# Retry validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("retry", [-1, -10])
def test_negative_retry_is_rejected(retry: int) -> None:
    console = Console(color=False, cls=False)

    with pytest.raises(ValueError, match="retry must be >= 0"):
        console.ask("Input:", retry=retry)


@pytest.mark.parametrize("retry", [True, False, 1.5, "3", None])
def test_invalid_retry_type_is_rejected(retry: object) -> None:
    console = Console(color=False, cls=False)

    with pytest.raises(TypeError, match="retry must be an integer"):
        console.ask("Input:", retry=retry)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Alias normalization
# ---------------------------------------------------------------------------


def test_default_aliases_are_present() -> None:
    assert "yes" in DEFAULT_YES
    assert "y" in DEFAULT_YES

    assert "no" in DEFAULT_NO
    assert "n" in DEFAULT_NO


def test_aliases_do_not_modify_defaults() -> None:
    aliases = ["custom"]

    normalized = Console._normalize_aliases(DEFAULT_YES, aliases)

    assert "custom" in normalized
    assert "custom" not in DEFAULT_YES


def test_aliases_accept_non_string_values() -> None:
    normalized = Console._normalize_aliases(
        DEFAULT_YES,
        [123, "yeah"],
    )

    assert "123" in normalized
    assert "yeah" in normalized


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------


def test_clear_uses_clear_command_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr(
        "vanta.app.os.name",
        "posix",
    )
    monkeypatch.setattr(
        "vanta.app.shutil.which",
        lambda command: "/usr/bin/clear" if command == "clear" else None,
    )

    run = Mock()
    monkeypatch.setattr("vanta.app.subprocess.run", run)

    console.clear()

    run.assert_called_once()


def test_clear_does_not_fail_when_command_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr(
        "vanta.app.os.name",
        "posix",
    )
    monkeypatch.setattr(
        "vanta.app.shutil.which",
        lambda _: None,
    )

    # Should simply do nothing.
    console.clear()


def test_clear_ignores_subprocess_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = Console(color=False, cls=False)

    monkeypatch.setattr(
        "vanta.app.os.name",
        "posix",
    )
    monkeypatch.setattr(
        "vanta.app.shutil.which",
        lambda _: "/usr/bin/clear",
    )

    monkeypatch.setattr(
        "vanta.app.subprocess.run",
        Mock(side_effect=OSError),
    )

    # Clearing is best-effort and must not crash.
    console.clear()


def test_constructor_clears_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear = Mock()

    monkeypatch.setattr(
        Console,
        "clear",
        clear,
    )

    Console(cls=True)

    clear.assert_called_once()


def test_constructor_can_skip_clear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear = Mock()

    monkeypatch.setattr(
        Console,
        "clear",
        clear,
    )

    Console(cls=False)

    clear.assert_not_called()


# ---------------------------------------------------------------------------
# Broken pipe handling
# ---------------------------------------------------------------------------


def test_print_ignores_broken_pipe() -> None:
    stream = Mock()
    stream.isatty.return_value = False
    stream.write.side_effect = BrokenPipeError

    console = Console(color=False, cls=False, stream=stream)

    # Should not raise.
    console.info("hello")


def test_raw_without_timestamp_ignores_broken_pipe() -> None:
    stream = Mock()
    stream.isatty.return_value = False
    stream.write.side_effect = BrokenPipeError

    console = Console(color=False, cls=False, stream=stream)

    # Should not raise.
    console.raw("hello", timestamp=False)

def test_colored_output_on_tty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = FakeStream(tty=True)

    console = Console(cls=False, stream=stream)

    monkeypatch.setattr(console, "_timestamp", lambda: "12:34:56")

    console.success("hello")

    output = stream.getvalue()

    assert "\x1b[" in output
    assert "SUCCESS" in output
    assert "hello" in output