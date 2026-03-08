"""
prefix_bootstrap.tui
~~~~~~~~~~~~~~~~~~~~~

Full-screen Textual TUI for the Gentoo Prefix bootstrap.

Replicates the interactive experience of the original ``bootstrap_interactive()``
shell function, including:

- The original Gentoo ASCII art banner.
- A conversational welcome wizard that asks the user for the prefix path.
- Environment variable sanity checks (LD_LIBRARY_PATH, PKG_CONFIG_PATH, etc.)
- A live stage-progress panel updated by the bootstrap workers.
- The same playful, slightly feminine tone with emoticons. :)

Usage::

    # Launch the TUI directly
    prefix-bootstrap tui

    # The TUI is also launched automatically when running without arguments
    python -m prefix_bootstrap

Keyboard shortcuts in the TUI:

    Q / Ctrl-C  Quit
    Enter       Confirm prompts
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
)

# ---------------------------------------------------------------------------
# ASCII art — preserved verbatim from the original bootstrap-prefix.sh :D
# ---------------------------------------------------------------------------

GENTOO_BANNER = (
    "\n"
    "                                             .\n"
    "       .vir.                                d$b\n"
    "    .d$$$$$$b.    .cd$$b.     .d$$b.   d$$$$$$$$$$$b  .d$$b.      .d$$b.\n"
    "    $$$$( )$$$b d$$$()$$$.   d$$$$$$$b Q$$$$$$$P$$$P.$$$$$$$b.  .$$$$$$$b.\n"
    "    Q$$$$$$$$$$B$$$$$$$$P\"  d$$$PQ$$$$b.   $$$$.   .$$$P' `$$$ .$$$P' `$$$\n"
    '      "$$$$$$$P Q$$$$$$$b  d$$$P   Q$$$$b  $$$$b   $$$$b..d$$$ $$$$b..d$$$\n'
    '     d$$$$$$P"   "$$$$$$$$ Q$$$     Q$$$$  $$$$$   `Q$$$$$$$P  `Q$$$$$$$P\n'
    '    $$$$$$$P       `"""""   ""        ""   Q$$$P     "Q$$$P"     "Q$$$P"\n'
    '    `Q$$P"                                  """\n'
)

WELCOME_TEXT = (
    "             Welcome to the Gentoo Prefix interactive installer!\n\n\n"
    "    I will attempt to install Gentoo Prefix on your system.  To do so,\n"
    "    I will ask you some questions first.    After that,  you will have to\n"
    "    practise patience as your computer and I try to figure out a way to\n"
    "    get a lot of software packages compiled.    If everything goes\n"
    "    according to plan, you will end up with what we call a Prefix install,\n"
    "    but by that time, I will tell you more.\n"
)

# Environment variables that the original script checks and rejects if set.
_CHECKED_ENV_VARS = [
    "ASFLAGS",
    "CFLAGS",
    "CPPFLAGS",
    "CXXFLAGS",
    "DYLD_LIBRARY_PATH",
    "GREP_OPTIONS",
    "LDFLAGS",
    "LD_LIBRARY_PATH",
    "LIBPATH",
    "PERL_MM_OPT",
    "PERL5LIB",
    "PKG_CONFIG_PATH",
    "PYTHONPATH",
    "ROOT",
    "CPATH",
    "LIBRARY_PATH",
]


# ---------------------------------------------------------------------------
# Welcome screen
# ---------------------------------------------------------------------------


class WelcomeScreen(Static):
    """Full-screen welcome panel shown before the wizard starts."""

    DEFAULT_CSS = """
    WelcomeScreen {
        border: double green;
        padding: 1 2;
        height: auto;
    }
    .banner {
        color: $success;
    }
    .welcome-text {
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(GENTOO_BANNER, classes="banner")
        yield Static(WELCOME_TEXT, classes="welcome-text")


# ---------------------------------------------------------------------------
# Environment check panel
# ---------------------------------------------------------------------------


class EnvCheckPanel(Static):
    """Displays the result of the environment variable sanity check."""

    DEFAULT_CSS = """
    EnvCheckPanel {
        height: auto;
        padding: 1;
    }
    .env-ok {
        color: $success;
    }
    .env-bad {
        color: $error;
    }
    """

    def compose(self) -> ComposeResult:
        bad_vars: list[str] = []
        for var in _CHECKED_ENV_VARS:
            if os.environ.get(var):
                bad_vars.append(var)
                yield Static(f"  uh oh, {var}={os.environ[var]!r} :(", classes="env-bad")
            else:
                yield Static(f"  it appears {var} is not set :)", classes="env-ok")

        if bad_vars:
            yield Static(
                "\nAhem, your shell environment contains some variables I'm allergic to:\n"
                f"  {' '.join(bad_vars)}\n"
                "These flags can and will influence the way packages compile.\n"
                "Please unset them and try again. :/",
                classes="env-bad",
            )


# ---------------------------------------------------------------------------
# Stage progress panel
# ---------------------------------------------------------------------------


class StageProgress(Static):
    """Shows per-stage progress bars and the current package being built."""

    current_stage: reactive[int] = reactive(0)
    current_pkg: reactive[str] = reactive("")
    stage_done: reactive[list[bool]] = reactive(lambda: [False, False, False])

    DEFAULT_CSS = """
    StageProgress {
        height: auto;
        border: round $primary;
        padding: 1 2;
    }
    .stage-label {
        color: $text-muted;
    }
    .stage-active {
        color: $primary;
        text-style: bold;
    }
    .stage-done-label {
        color: $success;
    }
    .pkg-label {
        color: $text;
        text-style: italic;
    }
    """

    STAGE_NAMES: ClassVar[list[str]] = [
        "Stage 1 — Essential GNU Tools",
        "Stage 2 — Build Toolchain",
        "Stage 3 — Portage Prerequisites",
    ]

    def compose(self) -> ComposeResult:
        for i, name in enumerate(self.STAGE_NAMES, start=1):
            yield Label(f"  Stage {i}: {name}", id=f"stage-label-{i}")
        yield Label("", id="current-pkg")

    def watch_current_stage(self, stage: int) -> None:
        for i in range(1, 4):
            lbl = self.query_one(f"#stage-label-{i}", Label)
            name = self.STAGE_NAMES[i - 1]
            if i < stage:
                lbl.update(f"  [green]✓[/green] Stage {i}: {name}")
            elif i == stage:
                lbl.update(f"  [bold cyan]▶[/bold cyan] Stage {i}: {name}")
            else:
                lbl.update(f"    Stage {i}: {name}")

    def watch_current_pkg(self, pkg: str) -> None:
        lbl = self.query_one("#current-pkg", Label)
        if pkg:
            lbl.update(f"  Building: [italic]{pkg}[/italic] ...")
        else:
            lbl.update("")


# ---------------------------------------------------------------------------
# Log panel
# ---------------------------------------------------------------------------


class BootstrapLog(RichLog):
    """Scrollable log panel showing bootstrap output."""

    DEFAULT_CSS = """
    BootstrapLog {
        height: 1fr;
        border: round $primary-darken-2;
    }
    """


# ---------------------------------------------------------------------------
# Main TUI App
# ---------------------------------------------------------------------------


class BootstrapTUI(App[None]):
    """The Gentoo Prefix bootstrap TUI application.

    Replicates the original ``bootstrap_interactive()`` experience in a
    proper full-screen terminal UI, with live progress updates as each
    package is compiled.  :D
    """

    TITLE = "Gentoo Prefix Bootstrap"
    SUB_TITLE = "Linux aarch64 (arm64)"
    CSS = """
    Screen {
        layout: vertical;
    }
    #wizard {
        height: auto;
        padding: 1 2;
    }
    #wizard-question {
        color: $text;
        margin-bottom: 1;
    }
    #wizard-input {
        width: 60;
    }
    #btn-row {
        layout: horizontal;
        height: auto;
        margin-top: 1;
    }
    Button {
        margin-right: 2;
    }
    #error-msg {
        color: $error;
        height: auto;
    }
    """

    BINDINGS: ClassVar[list[Binding | tuple[str, str] | tuple[str, str, str]]] = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._prefix: Path | None = None
        self._work_dir: Path | None = None
        self._wizard_done = False
        self._env_ok = True

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        yield WelcomeScreen()

        with Container(id="wizard"):
            yield Label("", id="wizard-question")
            yield Input(placeholder="", id="wizard-input")
            yield Label("", id="error-msg")
            with Container(id="btn-row"):
                yield Button("Continue", variant="primary", id="btn-continue")
                yield Button("Quit", variant="error", id="btn-quit")

        yield EnvCheckPanel()
        yield StageProgress(id="stage-progress")
        yield BootstrapLog(id="bootstrap-log", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        """Start the wizard after the app mounts."""
        self._start_wizard()

    def _start_wizard(self) -> None:
        """Present the first wizard prompt."""
        # Check root
        if os.getuid() == 0:
            self._show_error(
                "Hmmm, you appear to be root (UID 0).  The Gentoo Prefix people\n"
                "really discourage running Gentoo Prefix as root.  Refusing to help. :/"
            )
            return

        # Check bad env vars
        bad = [v for v in _CHECKED_ENV_VARS if os.environ.get(v)]
        if bad:
            self._show_error(
                f"Your environment has variables I'm allergic to: {', '.join(bad)}\n"
                "Please unset them and try again. :/"
            )
            return

        # Check arch
        machine = platform.machine().lower()
        if machine not in ("aarch64", "arm64"):
            self._show_error(
                f"Unsupported architecture '{machine}'.  "
                "This bootstrap only supports Linux aarch64 (arm64). :/"
            )
            return

        # Check OS
        if sys.platform != "linux":
            self._show_error("Only Linux is supported.  :/")
            return

        self._ask_prefix()

    def _ask_prefix(self) -> None:
        default = Path.home() / "gentoo"
        self.query_one("#wizard-question", Label).update(
            f"Ok!  Seems we can finally do something productive now.  :)\n\n"
            f"Where would you like your Gentoo Prefix to be installed?\n"
            f"I'll use [bold]{default}[/bold] if you just press Enter."
        )
        inp = self.query_one("#wizard-input", Input)
        inp.placeholder = str(default)
        inp.value = ""
        inp.focus()

    def _show_error(self, msg: str) -> None:
        self.query_one("#error-msg", Label).update(msg)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#btn-continue")
    def handle_continue(self) -> None:
        """Process the current wizard step."""
        if self._wizard_done:
            return
        inp = self.query_one("#wizard-input", Input)
        val = inp.value.strip()

        if self._prefix is None:
            # Prefix step
            default = Path.home() / "gentoo"
            self._prefix = Path(val) if val else default
            if not self._prefix.is_absolute():
                self._show_error("Your path needs to be absolute!  Try again. :/")
                return
            self._ask_work_dir()
        elif self._work_dir is None:
            # Work dir step
            default_wd = self._prefix / ".bootstrap-work"
            self._work_dir = Path(val) if val else default_wd
            self._wizard_done = True
            self._start_bootstrap()

    @on(Button.Pressed, "#btn-quit")
    def handle_quit(self) -> None:
        self.exit()

    @on(Input.Submitted)
    def handle_input_submitted(self) -> None:
        self.handle_continue()

    def _ask_work_dir(self) -> None:
        default_wd = self._prefix / ".bootstrap-work"  # type: ignore[operator]
        self.query_one("#wizard-question", Label).update(
            f"Great!  Prefix will be installed at [bold]{self._prefix}[/bold].\n\n"
            f"Where should I put temporary build files?\n"
            f"I'll use [bold]{default_wd}[/bold] if you just press Enter. :)"
        )
        inp = self.query_one("#wizard-input", Input)
        inp.placeholder = str(default_wd)
        inp.value = ""
        inp.focus()

    # ------------------------------------------------------------------
    # Bootstrap runner
    # ------------------------------------------------------------------

    @work(thread=True)
    def _start_bootstrap(self) -> None:
        """Run the bootstrap in a background thread, updating TUI live."""
        from prefix_bootstrap.bootstrap import (
            bootstrap_stage1,
            bootstrap_stage2,
            bootstrap_stage3,
        )
        from prefix_bootstrap.config import BootstrapConfig

        if self._prefix is None or self._work_dir is None:
            self.call_from_thread(self._show_error, "Prefix or work_dir not set — bug. :/")
            return

        self.call_from_thread(
            self.query_one("#wizard-question", Label).update,
            f"Alright!  Let me bootstrap Gentoo Prefix at [bold]{self._prefix}[/bold].  "
            f"This will take a while — please be patient!  :D",
        )
        # Remove the input/button widgets synchronously via post_message.
        try:
            self.query_one("#wizard-input", Input).display = False
            self.query_one("#btn-row", Container).display = False
        except NoMatches:
            pass  # widgets may already be hidden

        try:
            cfg = BootstrapConfig(  # type: ignore[call-arg]
                prefix=self._prefix,
                work_dir=self._work_dir,
            )
        except Exception as exc:
            self.call_from_thread(self._show_error, f"Configuration error: {exc} :/")
            return

        log_widget = self.query_one("#bootstrap-log", BootstrapLog)
        stage_widget = self.query_one("#stage-progress", StageProgress)

        def _log(msg: str) -> None:
            self.call_from_thread(log_widget.write, msg)

        def _set_stage(n: int) -> None:
            self.call_from_thread(setattr, stage_widget, "current_stage", n)

        def _set_pkg(name: str) -> None:
            self.call_from_thread(setattr, stage_widget, "current_pkg", name)

        # Monkey-patch einfo/eerror to also push to the TUI log.
        import prefix_bootstrap.bootstrap as bm

        _orig_einfo = bm.einfo
        _orig_eerror = bm.eerror

        def _tui_einfo(msg: str) -> None:
            _orig_einfo(msg)
            _log(f"[green]*[/green] {msg}")

        def _tui_eerror(msg: str) -> None:
            _orig_eerror(msg)
            _log(f"[red]!!![/red] {msg}")

        bm.einfo = _tui_einfo  # noqa: E501
        bm.eerror = _tui_eerror  # noqa: E501

        try:
            _set_stage(1)
            bootstrap_stage1(cfg)

            _set_stage(2)
            bootstrap_stage2(cfg)

            _set_stage(3)
            bootstrap_stage3(cfg)

            _set_stage(4)  # all done
            _set_pkg("")
            _log("[bold green]Bootstrap complete!  Happy Gentooing!  :D[/bold green]")
            self.call_from_thread(
                self.query_one("#wizard-question", Label).update,
                "[bold green]Bootstrap complete!  Happy Gentooing!  :D[/bold green]",
            )
        except Exception as exc:
            _log(f"[red]Bootstrap failed:[/red] {exc} :/")
            self.call_from_thread(self._show_error, f"Bootstrap failed: {exc} :/")
        finally:
            bm.einfo = _orig_einfo  # noqa: E501
            bm.eerror = _orig_eerror  # noqa: E501


def run_tui() -> None:
    """Launch the Gentoo Prefix bootstrap TUI.

    This is the entry point for ``prefix-bootstrap tui``.  :)
    """
    app = BootstrapTUI()
    app.run()
