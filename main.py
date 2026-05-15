import tkinter as tk
from gui import FrutariaApp
from database import setup_database, verify_and_add_initial_users
from login import LoginDialog


if __name__ == "__main__":
    setup_database()
    verify_and_add_initial_users()

    bootstrap = tk.Tk()
    bootstrap.withdraw()

    login_dialog = LoginDialog(bootstrap)
    bootstrap.wait_window(login_dialog)

    if login_dialog.user_data:
        bootstrap.destroy()
        app = FrutariaApp()
        app.logged_user = login_dialog.user_data
        app.deiconify()
        app.attributes("-fullscreen", True)
        app.is_fullscreen = True
        app.lift()
        app.setup_interface_by_role()
        app.show_startup_alerts()
        app.mainloop()
    else:
        bootstrap.destroy()
        print("Login cancelado. Aplicativo encerrado.")
