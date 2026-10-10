# Publishing EasyResearch

The same steps as for EasyClassifier (its `docs/PUBLISHING.md`), for this
repository.

## One-time setup

1. **Zenodo:** in Zenodo's GitHub settings, switch `ahmadhassant/easyresearch`
   On, so every GitHub release is archived with a DOI (metadata from
   `.zenodo.json`).
2. **PyPI:** in *Your account → Publishing*, add a pending publisher:
   project `easyresearch`, owner `ahmadhassant`, repository `easyresearch`,
   workflow `release.yml`, environment `pypi`.
3. **GitHub:** *Settings → Environments → New environment* named `pypi`.

## Every release

1. EasyClassifier first, if EasyResearch needs a new version of it; then
   update `pyproject.toml` (dependency range), `desktop/requirements.lock.txt`
   and `desktop/modules/classification.json`.
2. Change the version in `pyproject.toml`, `src/easyresearch/__init__.py`,
   `CITATION.cff` (`version`, `date-released`), the desktop version
   (`<Version>` in `EasyResearch.Desktop.csproj`, the footer in
   `MainWindow.xaml`, `PORTABLE-README.txt`) and the manifests if they
   change; add sections to `CHANGELOG.md` and `desktop/CHANGELOG.md`. The
   desktop and the package carry the same version number.
3. Check that the *tests* workflow is green on GitHub.
4. Run the *desktop release* workflow by hand (Actions → desktop release →
   Run workflow). It builds the setup program, installs it, checks it and
   uninstalls it. Download the `EasyResearchDesktop-setup` artifact, install
   it on a Windows computer, try each task and, ideally on a computer that
   never had Python, run `verify_portable.ps1` on the installed folder.
5. Draft a GitHub release with the new tag (e.g. `v0.1.0`). PyPI and Zenodo
   update automatically, and the *desktop release* workflow attaches the
   setup program to the release (it refuses a tag that does not match the
   desktop version).
6. After the first release, add the Zenodo DOI for all versions to
   `CITATION.cff` and a DOI badge to `README.md`.
