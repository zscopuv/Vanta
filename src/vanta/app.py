# src/vanta/app.py

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Callable, Iterable, TypeVar

from colorama import Fore, init

from .metadata import __version__, __desc__


init(autoreset=True)


T = TypeVar("T")
Output = Callable[[str], T]


VARIANTS: dict[str, tuple[str, str]] = {
    #             TEXT COLOR             BRACKET COLOR
    "success":  (  Fore.LIGHTGREEN_EX,    Fore.GREEN),
    "info":     (  Fore.LIGHTBLUE_EX,     Fore.BLUE),
    "warning":  (  Fore.LIGHTYELLOW_EX,   Fore.YELLOW),
    "error":    (  Fore.LIGHTRED_EX,      Fore.RED),
    "notice":   (  Fore.LIGHTCYAN_EX,     Fore.CYAN),
}

DEFAULT_YES = frozenset({"y", "1", "ok", "ye", "yes", "yep", "yy"})
DEFAULT_NO = frozenset({"n", "0", "no", "nah", "nn"})


class Console:
    """Small terminal console helper for Vanta."""

    def __init__(
        self,
        color: bool | None = None,
        cls: bool = True,
        *,
        stream: object | None = None,
    ) -> None:
        """
        Args:
            color:
                Whether ANSI colors should be used.

                ``None`` means automatic detection: colors are enabled only
                when the output stream is a TTY.

            cls:
                Whether to clear the terminal during initialization.

            stream:
                Output stream used for TTY detection. Defaults to stdout.
        """
        self._stream = stream if stream is not None else sys.stdout
        self._color = self._should_color(color)
        self._cls = cls

        if cls:
            self.clear()

    def _should_color(self, color: bool | None) -> bool:
        """Determine whether ANSI colors should be emitted."""
        if color is False:
            return False

        if color is True:
            # Explicitly requested, but don't emit ANSI when output isn't
            # capable of handling it.
            return self._is_tty()

        return self._is_tty()

    def _is_tty(self) -> bool:
        """Return whether the configured stream appears to be a TTY."""
        try:
            return bool(self._stream.isatty())  # type: ignore[attr-defined]
        except (AttributeError, OSError, ValueError):
            return False

    def clear(self) -> None:
        """Best-effort terminal clearing.

        Failure to clear the terminal is intentionally non-fatal.
        """
        # Windows
        if os.name == "nt":
            command = shutil.which("cls")
            if command:
                subprocess.run(
                    [command],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            # `cls` is normally a shell builtin, so fall back to cmd.
            try:
                subprocess.run(
                    ["cmd", "/c", "cls"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except (OSError, subprocess.SubprocessError):
                pass

            return

        # Unix-like systems
        command = shutil.which("clear")
        if command:
            try:
                subprocess.run(
                    [command],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except (OSError, subprocess.SubprocessError):
                pass

        # Last resort: ANSI clear sequence, but only for TTYs where
        # ANSI output is appropriate.
        if self._color:
            try:
                print("\033[2J\033[H", end="", file=self._stream)
            except (OSError, ValueError):
                pass

    @staticmethod
    def _timestamp() -> str:
        """Return the current local time as HH:MM:SS."""
        return datetime.now().strftime("%H:%M:%S")

    def _prefix(self, variant: str) -> str:
        """Build a colored or plain message prefix."""
        variant = variant.lower()

        if variant not in VARIANTS:
            variant = "info"

        text_color, bracket_color = VARIANTS[variant]
        name = variant.upper()

        if self._color:
            return f"{bracket_color}[{text_color}{name}{bracket_color}]{text_color} "

        return f"[{name}] "

    def _print(self, variant: str | None, message: str) -> None:
        """Print a timestamped message."""
        timestamp = f"[{self._timestamp()}]"

        if self._color:
            timestamp = f"{Fore.LIGHTBLACK_EX}{timestamp}"

        if variant is not None:
            output = f"{timestamp} {self._prefix(variant)}{message}"
        else:
            output = f"{timestamp} {message}"

        try:
            print(output, file=self._stream)
        except (BrokenPipeError, OSError):
            # Useful for commands such as `vanta | head`.
            return

    def info(self, message: str) -> None:
        self._print("info", message)

    def success(self, message: str) -> None:
        self._print("success", message)

    def warning(self, message: str) -> None:
        self._print("warning", message)

    def error(self, message: str) -> None:
        self._print("error", message)

    def notice(self, message: str) -> None:
        self._print("notice", message)

    def raw(self, message: str, timestamp: bool = True) -> None:
        if timestamp:
            self._print(None, message)
        else:
            try:
                print(message, file=self._stream)
            except (BrokenPipeError, OSError):
                return

    def ask(
        self,
        question: str,
        output: Output[T] = str,
        error_message: str | None = None,
        *,
        retry: int = 0,
    ) -> T:
        """
        Ask for input and convert it using ``output``.

        Args:
            question: Prompt shown to the user.
            output: Conversion/validation function.
            error_message: Message shown after invalid input.
            retry:
                Maximum number of retries after the initial attempt.
                ``0`` means retry indefinitely.

        Raises:
            ValueError: If ``retry`` is negative.
            EOFError: If stdin reaches EOF.
            KeyboardInterrupt: If the user interrupts input.
        """
        self._validate_retry(retry)

        attempts = 0

        while True:
            try:
                answer = input(f"{question} ").strip()
            except EOFError:
                self.error("Input ended unexpectedly.")
                raise
            except KeyboardInterrupt:
                self.raw("")
                raise

            try:
                return output(answer)
            except (ValueError, TypeError) as exc:
                attempts += 1

                output_name = getattr(
                    output,
                    "__name__",
                    type(output).__name__,
                )

                self.error(
                    error_message
                    if error_message is not None
                    else f"Invalid. Please use {output_name}."
                )

                if retry > 0 and attempts >= retry:
                    raise ValueError(
                        f"Maximum number of retries ({retry}) exceeded."
                    ) from exc

    def confirm(
        self,
        question: str,
        error_message: str | None = None,
        default: bool = True,
        *,
        retry: int = 0,
        alias_yes: Iterable[str] | None = None,
        alias_no: Iterable[str] | None = None,
    ) -> bool:
        """
        Ask a yes/no question.

        Args:
            question: Prompt shown to the user.
            error_message: Message shown for invalid input.
            default: Value returned when the user presses Enter.
            retry:
                Maximum number of retries after the initial attempt.
                ``0`` means retry indefinitely.
            alias_yes:
                Additional values accepted as yes.
            alias_no:
                Additional values accepted as no.
        """
        self._validate_retry(retry)

        yes = self._normalize_aliases(DEFAULT_YES, alias_yes)
        no = self._normalize_aliases(DEFAULT_NO, alias_no)

        options = "Y/n" if default else "y/N"
        attempts = 0

        while True:
            try:
                answer = input(f"{question} [{options}] ").strip().lower()
            except EOFError:
                self.error("Input ended unexpectedly.")
                raise
            except KeyboardInterrupt:
                self.raw("")
                raise

            if not answer:
                return default

            if answer in yes:
                return True

            if answer in no:
                return False

            attempts += 1

            self.error(
                error_message
                if error_message is not None
                else "Invalid. Please reply using 'yes' or 'no'."
            )

            if retry > 0 and attempts >= retry:
                raise ValueError(
                    f"Maximum number of retries ({retry}) exceeded."
                )

    @staticmethod
    def _normalize_aliases(
        defaults: Iterable[str],
        aliases: Iterable[str] | None,
    ) -> frozenset[str]:
        """Normalize and merge default and custom aliases."""
        values = set(defaults)

        if aliases is not None:
            values.update(
                str(alias).strip().lower()
                for alias in aliases
                if str(alias).strip()
            )

        return frozenset(values)

    @staticmethod
    def _validate_retry(retry: int) -> None:
        if isinstance(retry, bool) or not isinstance(retry, int):
            raise TypeError("retry must be an integer.")

        if retry < 0:
            raise ValueError("retry must be >= 0.")

    def _testall(self) -> None:
        self.info(f"Vanta {__version__}")
        self.success(f"Vanta {__version__}")
        self.warning(f"Vanta {__version__}")
        self.error(f"Vanta {__version__}")
        self.notice(f"Vanta {__version__}")
        self.raw(f"Vanta {__version__}")
        self.raw(f"Vanta {__version__}", False)