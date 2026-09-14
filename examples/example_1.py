from vanta import Console

app = Console()

favorite_number = app.ask("What is your favorite number?", int)

app.info(f"Your favorite number is {favorite_number}")