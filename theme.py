APP_THEME = {
    "bg": "#F3FBF5",
    "surface": "#FFFFFF",
    "surface_alt": "#ECFFF2",
    "surface_elevated": "#FFF7EC",
    "nav": "#0D4D2C",
    "nav_active": "#13653C",
    "nav_border": "#2B7A4D",
    "nav_muted": "#D8F4E1",
    "primary": "#12A150",
    "primary_dark": "#0C7139",
    "primary_soft": "#DBF7E6",
    "accent": "#FF8A1F",
    "accent_dark": "#D96C00",
    "accent_soft": "#FFF0DC",
    "text": "#143122",
    "text_muted": "#5E7466",
    "text_on_dark": "#F8FFF9",
    "border": "#CFE7D8",
    "card_edge": "#DCEFE2",
    "success": "#10A56E",
    "warning": "#D97706",
    "danger": "#D94841",
    "danger_soft": "#FFE1DF",
    "shadow": "#CFE6D7",
}


def configure_ttk_styles(style):
    theme = APP_THEME
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=theme["surface"],
        foreground=theme["text"],
        fieldbackground=theme["surface"],
        bordercolor=theme["border"],
        borderwidth=1,
        rowheight=36,
        font=("Segoe UI", 10),
    )
    style.map(
        "Treeview",
        background=[("selected", theme["primary_dark"])],
        foreground=[("selected", theme["text_on_dark"])],
    )
    style.configure(
        "Treeview.Heading",
        background=theme["surface_elevated"],
        foreground=theme["text"],
        relief="flat",
        borderwidth=0,
        font=("Segoe UI Semibold", 10),
        padding=(10, 10),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", theme["primary_soft"])],
    )
    style.configure(
        "TCombobox",
        padding=6,
        fieldbackground=theme["surface"],
        background=theme["surface"],
        foreground=theme["text"],
        bordercolor=theme["border"],
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", theme["surface"])],
        selectbackground=[("readonly", theme["surface"])],
        selectforeground=[("readonly", theme["text"])],
    )
    style.configure(
        "TScrollbar",
        background=theme["surface_alt"],
        troughcolor=theme["bg"],
        bordercolor=theme["bg"],
        arrowcolor=theme["text_muted"],
    )
