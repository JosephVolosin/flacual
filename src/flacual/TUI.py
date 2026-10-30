from pathlib import Path

from textual import log, on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import DataTable, DirectoryTree, Footer, Header, Input, Label

from src.flacual.metaflac import Song


class EditTag(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    EditTag { align: center middle; background: transparent; }
    EditTag > Vertical {
        width: 80;
        border: round $primary;
        height: auto;
        background: $surface;
    }
    """

    def __init__(self, label: str, value: str):
        super().__init__()
        self.label = label
        self.value = value

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Edit '{self.label}'")
            yield Input(self.value)

    def on_input_submitted(self, event: Input.Submitted):
        self.dismiss({"tag": self.label, "value": event.value})

    def action_cancel(self):
        self.dismiss(None)


class FLACTree(DirectoryTree):
    BINDINGS = [("1", "artist_for_directory", "Set Artist For Directory")]

    class SetArtistForDirectoryRequested(Message):
        def __init__(self, directory: Path):
            super().__init__()
            self.directory = directory

    def _get_directory_at_cursor(self):
        node = self.cursor_node
        if node is None or node.data is None:
            return None
        path = node.data.path
        return path if path.is_dir() else None

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        results: list[Path] = []

        for p in paths:
            if p.is_dir() or p.suffix.lower() == ".flac":
                results.append(p)

        return results

    def action_artist_for_directory(self):
        directory = self._get_directory_at_cursor()

        if directory:
            self.post_message(self.SetArtistForDirectoryRequested(directory))


class FlacualApp(App):
    CSS = """
    Screen {
        layers: base overlay;
    }

    Horizontal {
        height: 1fr;
    }

    DirectoryTree {
        width: 30%;
    }

    VerticalScroll {
        width: 70%;
        padding: 1;
    }

    #preview {
        width: 100%;
        height: auto;
    }

    DataTable {
        layer: base;
    }

    TagEditor {
        layer: overlay;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("d", "delete_item", "Delete Tag")]

    current_file: str | None = None
    curernt_file_obj: Song | None = None

    def __init_table(self):
        table_widget = self.query_one(DataTable)
        table_widget.add_columns("Tag Name", "Tag Value")
        table_widget.row_cursor_type = "row"

    def draw_song_on_table(self):
        table_widget = self.query_one(DataTable)
        table_widget.clear()
        if self.current_file_obj:
            tags = self.current_file_obj.list_tags()
            if tags:
                for tag_key, tag_value in tags.items():
                    table_widget.add_row(tag_key, tag_value, key=tag_key)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield FLACTree(self.library)
            with VerticalScroll():
                yield DataTable()
        yield Footer()

    def on_mount(self):
        self.__init_table()

    def action_delete_item(self):
        table_widget = self.query_one(DataTable)
        row_coord = table_widget.cursor_coordinate
        row_key, _ = table_widget.coordinate_to_cell_key(row_coord)
        tag_was_removed = self.current_file_obj.remove_tag(row_key.value)
        if tag_was_removed:
            log("Tag successfully removed!")
            # Re-draw table to show the update
            self.draw_song_on_table()
        else:
            log("Tag was unable to be removed.")

    @on(FLACTree.FileSelected)
    def handle_file_selection(self, event: FLACTree.FileSelected) -> None:
        self.current_file = event.path
        self.current_file_obj = Song(self.current_file)
        self.draw_song_on_table()

    @on(FLACTree.SetArtistForDirectoryRequested)
    def handle_set_artist_for_directory_requested(
        self, event: FLACTree.SetArtistForDirectoryRequested
    ):
        directory = event.directory

        def handle_mass_artist_update(data: dict):
            tag = data.get("tag", None)
            value = data.get("value", None)
            if tag is not None and value is not None:
                for directory_file in directory.rglob("*.flac"):
                    directory_file_song = Song(str(directory_file))
                    tag_was_set = directory_file_song.set_tag(tag, value)
                    if tag_was_set:
                        log("Tag successfully updated!")
                    else:
                        log("Tag was unable to be updated.")

        log("Setting artist for the whole directory: " + str(directory))
        self.push_screen(EditTag("ARTIST", ""), handle_mass_artist_update)

    def handle_tag_update(self, data: dict):
        tag = data.get("tag", None)
        value = data.get("value", None)
        if tag is not None and value is not None:
            tag_was_set = self.current_file_obj.set_tag(tag, value)
            if tag_was_set:
                log("Tag successfully updated!")
                # Re-draw table to show the update
                self.draw_song_on_table()
            else:
                log("Tag was unable to be updated.")

    def on_data_table_cell_selected(self, event: DataTable.CellSelected):
        tag = event.cell_key.row_key.value
        value = str(event.value)

        self.push_screen(EditTag(tag, value), self.handle_tag_update)

    def __init__(self, library: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.library = library
