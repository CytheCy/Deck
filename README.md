# Deck

Deck is a small Fedora/KDE desktop app that draws cards at random from `.deck` files. A `.deck` file is UTF-8 plain text, and every non-empty line is one card. A card is never repeated until every card in that file has appeared; then Deck automatically starts a fresh randomized round.

## Run it

Fedora 40 or newer with Python 3.10+ is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m deck_app
```

On first launch, select the `examples` folder or any folder containing `.deck` files. If a folder contains several deck files, choose the active deck from the footer list.

## Controls

- **Next**, `Space`, or `Right Arrow`: randomly draw an unseen card.
- **Add card** or `Ctrl+N`: append one card to the selected `.deck` file.
- **Edit** or `Ctrl+E`: update the card currently in view.
- **Settings** or `Ctrl+,`: choose a different deck folder and switch between light and dark themes.

Deck saves the selected folder, selected file, theme, and each deck's seen line numbers to `$XDG_DATA_HOME/deck/state.json` (normally `~/.local/share/deck/state.json`). State is written as soon as a card is displayed, so closing the window cannot cause that card to repeat on the next launch.

Blank lines are ignored. Existing cards can be edited with any text editor; editing or reordering existing lines safely starts a fresh round. Appending cards preserves the current round.

## Install as a user application

After activating the virtual environment, install the package and desktop entry:

```bash
pip install .
install -Dm644 packaging/io.github.deck.Deck.desktop "$HOME/.local/share/applications/io.github.deck.Deck.desktop"
install -Dm644 packaging/io.github.deck.Deck.xml "$HOME/.local/share/mime/packages/io.github.deck.Deck.xml"
update-mime-database "$HOME/.local/share/mime"
update-desktop-database "$HOME/.local/share/applications"
```

The `deck` command will then be available while that Python environment is active. For a permanent launcher, use a tool such as `pipx install .` and ensure `~/.local/bin` is on your `PATH`.

After installation, `.deck` files appear with Deck in the file manager's **Open With** menu. Opening one this way uses that file for the current app session only; launching Deck normally still opens the saved deck folder and selected file from Settings.

## Tests

```bash
python -m unittest discover -v
```

Toolbar icons are from [Boxicons v2](https://github.com/atisawd/boxicons), used under the MIT license included in `assets/icons/LICENSE`.
