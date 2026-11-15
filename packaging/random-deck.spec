Name:           random-deck
Version:        1.0.0
Release:        1%{?dist}
Summary:        Random card viewer for .deck files
License:        LicenseRef-Unknown
Source0:        random_deck-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-pyside6
BuildRequires:  desktop-file-utils
Requires:       python3-pyside6
Requires:       shared-mime-info
Requires:       hicolor-icon-theme

%description
Deck draws cards from plain-text .deck files without repeating a card until
every card has appeared. The package includes a KDE launcher and file type
association.

%prep
%autosetup -n random_deck-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files deck_app
rm %{buildroot}%{_datadir}/deck/assets/icons/LICENSE

%check
desktop-file-validate packaging/io.github.deck.Deck.desktop
QT_QPA_PLATFORM=offscreen %{python3} -m unittest discover -s tests -v

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/deck
%{_datadir}/applications/io.github.deck.Deck.desktop
%{_datadir}/icons/hicolor/scalable/apps/io.github.deck.Deck.svg
%{_datadir}/icons/hicolor/scalable/mimetypes/application-x-deck.svg
%{_datadir}/mime/packages/io.github.deck.Deck.xml
%dir %{_datadir}/deck
%dir %{_datadir}/deck/assets
%dir %{_datadir}/deck/assets/icons
%{_datadir}/deck/assets/icons/*.svg
%license assets/icons/LICENSE

%changelog
* Sun Nov 15 2026 Deck contributors - 1.0.0-1
- Add Fedora RPM packaging with desktop and .deck integration
