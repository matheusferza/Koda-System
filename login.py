import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from branding import (
    APP_DESCRIPTION,
    APP_NAME_MULTILINE,
    COPYRIGHT_LABEL,
    LOGIN_HIGHLIGHTS,
    POWERED_BY_LABEL,
    format_window_title,
)
from database import check_password, get_db_connection
from theme import APP_THEME
from utils import get_app_icon_path, get_app_logo_path


class LoginDialog(tk.Toplevel):
    def __init__(self, master, balanca_instance=None):
        super().__init__(master)
        self.master = master
        self.balanca_instance = balanca_instance
        self.user_data = None
        self.theme = APP_THEME
        self.icon_tk = None
        self.logo_image = None
        self._current_logo_size = None

        self.title(format_window_title("Acesso"))
        self.attributes("-fullscreen", True)
        self.configure(bg=self.theme["bg"])
        self.protocol("WM_DELETE_WINDOW", self.on_close_dialog)
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)
        self._load_icon()

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Entre com seu usuário e senha.")

        self._build_layout()
        self.after(120, self.user_entry.focus_set)

    def _load_icon(self):
        try:
            icon_image = Image.open(get_app_icon_path())
            self.icon_tk = ImageTk.PhotoImage(icon_image)
            self.iconphoto(False, self.icon_tk)
        except Exception:
            self.icon_tk = None

    def _build_layout(self):
        self.canvas = tk.Canvas(self, bg=self.theme["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._render_scene)

        self.card = tk.Frame(self.canvas, bg=self.theme["surface"], bd=0, highlightthickness=0)
        self.card_window = self.canvas.create_window(0, 0, window=self.card, anchor="center")

        self.left_panel = tk.Frame(self.card, bg=self.theme["nav"])
        self.right_panel = tk.Frame(self.card, bg=self.theme["surface"])
        self.card.grid_columnconfigure(0, weight=1)
        self.card.grid_columnconfigure(1, weight=1)
        self.card.grid_rowconfigure(0, weight=1)
        self.card.grid_rowconfigure(1, weight=1)

        self.brand_title = tk.Label(self.left_panel, justify="left", bg=self.theme["nav"], fg=self.theme["text_on_dark"])
        self.brand_title.pack(anchor="w")
        self.brand_copy = tk.Label(self.left_panel, justify="left", bg=self.theme["nav"], fg="#DDEBDF")
        self.brand_copy.pack(anchor="w")

        self.logo_label = tk.Label(self.left_panel, bg=self.theme["nav"])
        self.logo_label.pack(anchor="w")

        self.highlight_labels = []
        for text in LOGIN_HIGHLIGHTS:
            label = tk.Label(
                self.left_panel,
                text=f"• {text}",
                justify="left",
                bg=self.theme["nav"],
                fg=self.theme["text_on_dark"],
            )
            label.pack(anchor="w")
            self.highlight_labels.append(label)

        self.access_title = tk.Label(self.right_panel, bg=self.theme["surface"], fg=self.theme["text"])
        self.access_title.pack(anchor="w")
        self.access_copy = tk.Label(self.right_panel, bg=self.theme["surface"], fg=self.theme["text_muted"], justify="left")
        self.access_copy.pack(anchor="w")

        self.user_label = tk.Label(self.right_panel, bg=self.theme["surface"], fg=self.theme["text"])
        self.user_label.pack(anchor="w")
        self.user_entry = self._build_field(self.right_panel, self.username_var)

        self.password_label = tk.Label(self.right_panel, bg=self.theme["surface"], fg=self.theme["text"])
        self.password_label.pack(anchor="w")
        self.password_entry = self._build_field(self.right_panel, self.password_var, show="*")

        self.show_password = tk.Checkbutton(
            self.right_panel,
            text="Mostrar senha",
            variable=self.show_password_var,
            command=self._toggle_password,
            bg=self.theme["surface"],
            fg=self.theme["text_muted"],
            activebackground=self.theme["surface"],
            activeforeground=self.theme["text"],
            selectcolor=self.theme["surface"],
            relief="flat",
            anchor="w",
        )
        self.show_password.pack(anchor="w")

        self.login_button = tk.Button(
            self.right_panel,
            text="Entrar no sistema",
            command=self.perform_login,
            bg=self.theme["primary"],
            fg=self.theme["text_on_dark"],
            activebackground=self.theme["primary_dark"],
            activeforeground=self.theme["text_on_dark"],
            relief="flat",
            cursor="hand2",
        )
        self.login_button.pack(fill="x")

        self.status_label = tk.Label(
            self.right_panel,
            textvariable=self.status_var,
            justify="left",
            bg=self.theme["surface"],
            fg=self.theme["text_muted"],
        )
        self.status_label.pack(anchor="w")

        self.footer_label = tk.Label(
            self.right_panel,
            bg=self.theme["surface"],
            fg=self.theme["text_muted"],
            justify="left",
        )
        self.footer_label.pack(anchor="w")

        self.user_entry.bind("<Return>", lambda _event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda _event: self.perform_login())

    def _build_field(self, parent, variable, show=""):
        entry = tk.Entry(
            parent,
            textvariable=variable,
            show=show,
            relief="solid",
            bd=1,
            bg="#FFFFFF",
            fg=self.theme["text"],
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["primary"],
            insertbackground=self.theme["text"],
        )
        entry.pack(fill="x")
        return entry

    def _apply_responsive_style(self, width, height):
        compact_mode = width <= 1180 or height <= 820
        ultra_compact = width <= 980 or height <= 720

        card_width = min(max(width - (32 if ultra_compact else 56), 820 if ultra_compact else 900), 960)
        card_height = min(max(height - (42 if ultra_compact else 70), 560 if ultra_compact else 620), 620)
        left_width = int(card_width * (0.39 if ultra_compact else 0.44))
        right_width = card_width - left_width

        side_pad = 24 if ultra_compact else 36
        top_pad = 22 if ultra_compact else 34
        brand_font = ("Segoe UI Black", 20 if ultra_compact else 28)
        copy_font = ("Segoe UI", 9 if ultra_compact else 11)
        title_font = ("Segoe UI Semibold", 20 if compact_mode else 23)
        field_label_font = ("Segoe UI Semibold", 10)
        field_font = ("Segoe UI", 11 if compact_mode else 12)
        status_font = ("Segoe UI", 9)
        button_font = ("Segoe UI Semibold", 10 if compact_mode else 11)
        wrap_left = max(left_width - (side_pad * 2), 220)
        wrap_right = max(right_width - (side_pad * 2), 260)
        field_ipady = 7 if compact_mode else 9
        button_pady = 10 if compact_mode else 12
        logo_size = 72 if ultra_compact else 104 if compact_mode else 124

        for panel in (self.left_panel, self.right_panel):
            panel.configure(padx=side_pad, pady=top_pad)

        self.card.grid_columnconfigure(0, weight=0, minsize=left_width)
        self.card.grid_columnconfigure(1, weight=1, minsize=right_width)
        self.card.grid_rowconfigure(0, weight=1)
        if self.left_panel.winfo_manager() != "grid" or self.right_panel.winfo_manager() != "grid":
            self.left_panel.grid_forget()
            self.right_panel.grid_forget()
            self.left_panel.grid_propagate(False)
            self.right_panel.grid_propagate(False)
            self.left_panel.grid(row=0, column=0, sticky="nsew")
            self.right_panel.grid(row=0, column=1, sticky="nsew")


        self.brand_title.config(text=APP_NAME_MULTILINE, font=brand_font)
        self.brand_copy.config(
            text=APP_DESCRIPTION,
            wraplength=wrap_left,
            font=copy_font,
        )
        self.brand_copy.pack_configure(pady=(18 if compact_mode else 24, 14 if ultra_compact else 18))
        self.logo_label.pack_configure(pady=(0, 26 if ultra_compact else 36))

        for label in self.highlight_labels:
            label.config(font=("Segoe UI", 9 if compact_mode else 10), wraplength=wrap_left)
            label.pack_configure(pady=6 if ultra_compact else 8)

        self.access_title.config(text="Acesso ao sistema", font=title_font)
        self.access_copy.config(
            text="Use as credenciais cadastradas para continuar.",
            font=copy_font,
            wraplength=wrap_right,
        )
        self.access_copy.pack_configure(pady=(6, 18 if compact_mode else 24))

        self.user_label.config(text="Usuário", font=field_label_font)
        self.user_label.pack_configure(pady=(0, 6))
        self.password_label.config(text="Senha", font=field_label_font)
        self.password_label.pack_configure(pady=(0, 6))

        for entry in (self.user_entry, self.password_entry):
            entry.config(font=field_font)
            entry.pack_configure(ipady=field_ipady, pady=(0, 12 if compact_mode else 16))

        self.show_password.config(font=("Segoe UI", 9))
        self.show_password.pack_configure(pady=(2, 14 if compact_mode else 18))

        self.login_button.config(
            font=button_font,
            padx=14,
            pady=button_pady,
            text="Entrar no sistema",
        )
        self.login_button.pack_configure(pady=(0, 10 if compact_mode else 12))

        self.status_label.config(font=status_font, wraplength=wrap_right)
        self.status_label.pack_configure(pady=(8, 0))
        self.footer_label.config(
            text=f"{POWERED_BY_LABEL}\n{COPYRIGHT_LABEL}",
            font=status_font,
            wraplength=wrap_right,
        )
        self.footer_label.pack_configure(pady=(18 if compact_mode else 24, 0))

        self._load_logo(logo_size)
        self.canvas.itemconfigure(self.card_window, width=card_width, height=card_height)

    def _load_logo(self, size):
        if self._current_logo_size == size and self.logo_image is not None:
            return
        try:
            image = Image.open(get_app_logo_path()).resize((size, size), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(image)
            self.logo_label.config(image=self.logo_image, text="")
            self._current_logo_size = size
            return
        except Exception:
            self.logo_image = None
            self._current_logo_size = None
            self.logo_label.config(image="", text="")

    def _render_scene(self, event):
        width = max(event.width, 640)
        height = max(event.height, 480)
        self.canvas.delete("bg")
        self.canvas.create_rectangle(0, 0, width, height, fill=self.theme["bg"], outline="", tags="bg")
        self.canvas.create_oval(
            -120,
            -80,
            min(width * 0.36, 420),
            min(height * 0.55, 420),
            fill=self.theme.get("primary_soft", "#E6F1E2"),
            outline="",
            tags="bg",
        )
        self.canvas.create_oval(
            width - min(width * 0.28, 380),
            40,
            width + 140,
            min(height * 0.78, 620),
            fill=self.theme.get("accent_soft", "#FFE9D2"),
            outline="",
            tags="bg",
        )
        self.canvas.create_oval(
            width - min(width * 0.22, 260),
            height - min(height * 0.26, 240),
            width + 60,
            height + 80,
            fill=self.theme.get("surface_alt", "#DCEBDD"),
            outline="",
            tags="bg",
        )
        self._apply_responsive_style(width, height)
        self.canvas.coords(self.card_window, width / 2, height / 2)

    def _toggle_password(self):
        self.password_entry.config(show="" if self.show_password_var.get() else "*")

    def _toggle_fullscreen(self, _event=None):
        is_fullscreen = bool(self.attributes("-fullscreen"))
        self.attributes("-fullscreen", not is_fullscreen)

    def _exit_fullscreen(self, _event=None):
        self.attributes("-fullscreen", False)

    def perform_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            self.status_var.set("Preencha usuário e senha para continuar.")
            messagebox.showwarning("Atenção", "Por favor, preencha usuário e senha.", parent=self)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, cargo, senha FROM funcionarios WHERE usuario = ?", (username,))
        user_info_db = cursor.fetchone()
        conn.close()

        if user_info_db and check_password(password, user_info_db[3]):
            self.user_data = {
                "id": user_info_db[0],
                "nome": user_info_db[1],
                "cargo": user_info_db[2],
            }
            self.destroy()
            return

        self.password_var.set("")
        self.status_var.set("Credenciais inválidas. Verifique os dados e tente novamente.")
        messagebox.showerror("Acesso negado", "Usuário ou senha incorretos.", parent=self)
        self.user_entry.focus_set()

    def on_close_dialog(self):
        self.user_data = None
        self.destroy()
