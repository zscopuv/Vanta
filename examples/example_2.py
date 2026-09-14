from vanta import Console

app = Console()

confirmed = app.confirm("Are you sure you want to delete this? ")

if confirmed:
    app.notice("Photos deleted")
else:
    app.notice("Operation aborted")