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
- `Down Arrow` and `Up Arrow`: move through sections of the current card separated by `|` characters. Each card starts with its first section showing.
- **Add card** or `Ctrl+N`: append one card to the selected `.deck` file.
- **Show List** or `Ctrl+L`: browse and search all cards; activate one to show it.
- **Edit** or `Ctrl+E`: update the card currently in view. The edit window's **Cut** button copies the card to the clipboard and removes it from the deck.
- **Settings** or `Ctrl+,`: choose a different deck folder and select Catppuccin Mocha, Tokyo Night, Everforest Dark, or System. Changes are saved immediately. System follows the desktop's light or dark appearance at launch.

Deck saves the selected folder, selected file, theme, and each deck's seen line numbers to `$XDG_DATA_HOME/deck/state.json` (normally `~/.local/share/deck/state.json`). State is written as soon as a card is displayed, so closing the window cannot cause that card to repeat on the next launch.

Blank lines are ignored. Existing cards can be edited with any text editor; editing or reordering existing lines safely starts a fresh round. Appending cards preserves the current round.

## Install as a user application

After activating the virtual environment, install the package and desktop entry:

```bash
pip install .
install -Dm644 packaging/io.github.deck.Deck.desktop "$HOME/.local/share/applications/io.github.deck.Deck.desktop"
install -Dm644 assets/io.github.deck.Deck.svg "$HOME/.local/share/icons/hicolor/scalable/apps/io.github.deck.Deck.svg"
install -Dm644 assets/application-x-deck.svg "$HOME/.local/share/icons/hicolor/scalable/mimetypes/application-x-deck.svg"
install -Dm644 packaging/io.github.deck.Deck.xml "$HOME/.local/share/mime/packages/io.github.deck.Deck.xml"
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor"
update-mime-database "$HOME/.local/share/mime"
update-desktop-database "$HOME/.local/share/applications"
```

The `deck` command will then be available while that Python environment is active. For a permanent launcher, use a tool such as `pipx install .` and ensure `~/.local/bin` is on your `PATH`.

After installation, `.deck` files appear with Deck in the file manager's **Open With** menu. Opening one this way uses that file for the current app session only; launching Deck normally still opens the saved deck folder and selected file from Settings.

## Build and install a Fedora RPM

Pushing a `v1.0.0` tag to GitHub runs the Fedora 44 RPM build and its tests. When
the workflow succeeds, the RPM is attached to the `v1.0.0` GitHub Release.
Download that RPM from the repository's Releases page and install it with
`sudo dnf install ./random-deck-1.0.0-1.fc44.noarch.rpm`.

Install the build tools and dependencies, then build from this checkout:

```bash
sudo dnf install rpm-build python3-build python3-devel python3-setuptools pyproject-rpm-macros python3-pyside6 desktop-file-utils
python3 -m build --sdist
mkdir -p "$HOME/rpmbuild/SOURCES" "$HOME/rpmbuild/SPECS"
cp dist/random_deck-1.0.0.tar.gz "$HOME/rpmbuild/SOURCES/"
cp packaging/random-deck.spec "$HOME/rpmbuild/SPECS/"
rpmbuild -ba "$HOME/rpmbuild/SPECS/random-deck.spec"
sudo dnf install "$HOME/rpmbuild/RPMS/noarch/random-deck-1.0.0-1"*.noarch.rpm
```

The RPM installs the Deck launcher, the supplied icon, and a matching icon for `.deck` files. KDE's application menu and Dolphin use these system-wide files. The desktop entry also makes Deck available in **Open With** for `.deck` files; set it as the default application in Dolphin if desired.

## Tests

```bash
python -m unittest discover -v
```

Toolbar icons are from [Boxicons v2](https://github.com/atisawd/boxicons), used under the MIT license included in `assets/icons/LICENSE`.
