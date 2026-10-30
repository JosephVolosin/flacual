from src.flacual.TUI import FlacualApp
from src.flacual.settings import settings
from src.flacual.metaflac import is_metaflac_callable

if __name__ == "__main__":
    if not is_metaflac_callable():
        print("'metaflac' was not found. Install it!")
    app = FlacualApp(settings.library)
    app.run()
    
