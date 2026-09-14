![vanta](https://i.ibb.co/q3HFNJV1/image.jpg)
A lightweight Python toolkit for beautiful, structured CLI output.

---

Vanta provides a simple `Console` class for building clean command-line interfaces with:

- Colored log messages
- Timestamps
- Cross-platform terminal clearing
- Typed user input
- Yes/no confirmation prompts
- Optional color output
- Optional automatic screen clearing

## Installation

### From source

Clone the repository:

```bash
pip install vanta
````

Then in your IDE:

```python
from vanta import Console
```

## Quick Start

```python
import vanta

console = vanta.Console()

console.info("Hello, world!")
console.success("Operation completed.")
console.warning("Something might be wrong.")
console.error("Something went wrong.")
console.notice("Please take note.")
```

Example output:

```js
[16:42:10] [INFO] Hello, world!
[16:42:10] [SUCCESS] Operation completed.
[16:42:10] [WARNING] Something might be wrong.
[16:42:10] [ERROR] Something went wrong.
[16:42:10] [NOTICE] Please take note.
```

When colors are enabled, each message type is displayed with its own color.

---

## Console

Create a console instance with:

```python
console = vanta.Console()
```

By default, Vanta:

* Enables colors
* Clears the terminal when the console is created

Both behaviors can be configured:

```python
console = vanta.Console(
    color=False,
    cls=False,
)
```

### Parameters

| Parameter | Type   | Default | Description                         |
| --------- | ------ | ------: | ----------------------------------- |
| `color`   | `bool` |  `True` | Enable or disable colored output    |
| `cls`     | `bool` |  `True` | Clear the terminal when initialized |

---

## Logging

Vanta provides five message variants.

### Info

```python
console.info("This is an informational message.")
```

### Success

```python
console.success("Everything went well!")
```

### Warning

```python
console.warning("Be careful.")
```

### Error

```python
console.error("Something went wrong.")
```

### Notice

```python
console.notice("Please take note of this.")
```

All messages include a timestamp.

---

## Raw Output

Use `raw()` when you want to output a message without a variant prefix.

```python
console.raw("Hello!")
```

By default, the timestamp is still displayed.

To remove the timestamp:

```python
console.raw("Hello!", timestamp=False)
```

Output:

```text
Hello!
```

---

## Clearing the Terminal

The terminal can be cleared manually:

```python
console.clear()
```

Vanta automatically uses the appropriate command for the operating system:

* Windows: `cmd /c cls`
* Linux/macOS: `clear`

---

## User Input

The `ask()` method allows you to request and convert user input.

```python
name = console.ask("What is your name:")
```

Since the default output type is `str`, this returns the entered text.

### Integers

```python
age = console.ask("How old are you:", int)
```

If the user enters:

```text
18
```

`age` will be an `int`.

Invalid input is automatically rejected:

```text
How old are you: abc
[16:45:21] [ERROR] Invalid. Please use int.
How old are you:
```

### Floating-point numbers

```python
price = console.ask("Enter the price:", float)
```

### Custom converters

`ask()` accepts any callable that takes a `str` and returns the desired type.

For example:

```python
def parse_name(value: str) -> str:
    value = value.strip()

    if not value:
        raise ValueError

    return value.title()


name = console.ask("Name:", parse_name)
```

### Custom error messages

You can provide your own error message:

```python
age = console.ask(
    "Age:",
    int,
    "Please enter a valid number."
)
```

---

## Confirmation Prompts

Use `confirm()` for yes/no questions:

```python
if console.confirm("Continue?"):
    print("Continuing...")
```

The default behavior is:

```text
Continue? [Y/n]
```

Pressing **Enter** accepts the default (`True`).

### Default to No

Set `default=False`:

```python
if console.confirm("Delete this file?", default=False):
    print("Deleting...")
```

The prompt becomes:

```text
Delete this file? [y/N]
```

Pressing **Enter** now returns `False`.

### Accepted Answers

Yes:

```text
y
1
ok
ye
yes
yep
yy
```

No:

```text
n
0
no
nah
nn
```

Input is case-insensitive.

### Custom Error Messages

```python
console.confirm(
    "Continue?",
    error_message="Please answer with yes or no."
)
```

---

## Disabling Colors

Colors can be disabled when creating the console:

```python
console = vanta.Console(color=False)
```

Output will then use plain text:

```text
[16:45:21] [INFO] Hello!
```

This can be useful when output is being redirected to a file or another program.

---

## API Reference

### `Console`

```python
Console(
    color: bool = True,
    cls: bool = True
)
```

### `clear()`

```python
console.clear() -> None
```

Clears the terminal.

### `info()`

```python
console.info(message: str) -> None
```

Prints an informational message.

### `success()`

```python
console.success(message: str) -> None
```

Prints a success message.

### `warning()`

```python
console.warning(message: str) -> None
```

Prints a warning message.

### `error()`

```python
console.error(message: str) -> None
```

Prints an error message.

### `notice()`

```python
console.notice(message: str) -> None
```

Prints a notice message.

### `raw()`

```python
console.raw(
    message: str,
    timestamp: bool = True
) -> None
```

Prints unclassified output.

### `ask()`

```python
console.ask(
    question: str,
    output: Callable[[str], T] = str,
    error_message: str | None = None
) -> T
```

Prompts the user for input and converts it using `output`.

### `confirm()`

```python
console.confirm(
    question: str,
    error_message: str | None = None,
    default: bool = True
) -> bool
```

Prompts the user for a yes/no response.

---

## Version

Current version: **0.1.0**

Vanta is currently in early development. The API may change between releases before reaching a stable `1.0.0` release.

## License

See `LICENSE` for license information.