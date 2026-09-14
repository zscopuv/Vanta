# src/vanta/app.py

import os
import subprocess
from datetime import datetime
from typing import Callable, TypeVar

from colorama import Fore, init

from .metadata import __version__, __desc__


init(autoreset=True)


T = TypeVar("T")


VARIANTS = {
    #            TEXT_COLOR             BRACKET_COLOR
    "success": (  Fore.LIGHTGREEN_EX  ,  Fore.GREEN),
    "info":    (  Fore.LIGHTBLUE_EX   ,  Fore.BLUE),
    "warning": (  Fore.LIGHTYELLOW_EX ,  Fore.YELLOW),
    "error":   (  Fore.LIGHTRED_EX    ,  Fore.RED),
    "notice":  (  Fore.LIGHTCYAN_EX   ,  Fore.CYAN),
}


class Console:

    def __init__(self, color: bool = True, cls: bool = True) -> None:
        self._color = color
        self._cls = cls

        if cls:
            self.clear()

    def clear(self) -> None:
        command = ["cmd", "/c", "cls"] if os.name == "nt" else ["clear"]
        subprocess.run(command, check=False)

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _prefix(self, variant: str) -> str:
        if variant not in VARIANTS:
            variant = "info"

        text_color, bracket_color = VARIANTS[variant]
        name = variant.upper()

        if self._color:
            return f"{bracket_color}[{text_color}{name}{bracket_color}]{text_color} "

        return f"[{name}] "

    def _print(self, variant: str | None, message: str) -> None:
        timestamp = f"[{self._timestamp()}]"

        if self._color:
            timestamp = f"{Fore.LIGHTBLACK_EX}{timestamp}"

        if variant is not None:
            print(f"{timestamp} {self._prefix(variant)}{message}")
        else:
            print(f"{timestamp} {message}")

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
            print(message)

    def ask(
        self,
        question: str,
        output: Callable[[str], T] = str,
        error_message: str | None = None,
    ) -> T:
        while True:
            answer = input(f"{question} ").strip()

            try:
                return output(answer)

            except (ValueError, TypeError):
                output_name = getattr(output, "__name__", type(output).__name__)
                self.error(
                    error_message
                    if error_message
                    else f"Invalid. Please use {output_name}."
                )

    def confirm(
        self,
        question: str,
        error_message: str | None = None,
        default: bool = True,
    ) -> bool:
        yes = {"y", "1", "ok", "ye", "yes", "yep", "yy"}
        no = {"n", "0", "no", "nah", "nn"}

        options = "Y/n" if default else "y/N"

        while True:
            answer = input(f"{question} [{options}] ").strip().lower()

            if not answer:
                return default

            if answer in yes:
                return True

            if answer in no:
                return False

            self.error(
                error_message
                if error_message
                else "Invalid. Please reply using 'yes' or 'no'."
            )

    def _testall(self) -> None:
        self.info(f"Vanta {__version__}")
        self.success(f"Vanta {__version__}")
        self.warning(f"Vanta {__version__}")
        self.error(f"Vanta {__version__}")
        self.notice(f"Vanta {__version__}")
        self.raw(f"Vanta {__version__}")
        self.raw(f"Vanta {__version__}", False)