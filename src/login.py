"""
login.py
========
Pantalla de inicio de sesión para el Sistema de Gestión.
Si la autenticación es exitosa, lanza la aplicación principal.
"""

import customtkinter as ctk
from tkinter import messagebox
import database as db
import styles as s
from main import App  # Importamos tu clase App del main.py

s.aplicar_tema()


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Iniciar Sesión — Cantina R.R.")
        self.geometry("400x480")
        self.configure(fg_color=s.C_BG)
        self.eval("tk::PlaceWindow . center")  # Centrar en la pantalla
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        # Contenedor principal tipo tarjeta
        card = ctk.CTkFrame(
            self,
            corner_radius=s.CORNER_CARD,
            fg_color=s.C_CARD,
            border_width=2,
            border_color=s.C_BORDER,
        )
        card.pack(expand=True, fill="both", padx=30, pady=40)

        # Título
        ctk.CTkLabel(
            card, text="Bienvenido", font=s.f_titulo(), text_color=s.C_TEXT
        ).pack(pady=(30, 5))

        ctk.CTkLabel(
            card,
            text="Ingresa tus credenciales",
            font=s.f_normal(),
            text_color=s.C_SUBTEXT,
        ).pack(pady=(0, 30))

        # Inputs
        self.e_usuario = ctk.CTkEntry(
            card,
            placeholder_text="Usuario",
            font=s.f_normal(),
            height=s.BTN_HEIGHT,
            corner_radius=s.CORNER,
        )
        self.e_usuario.pack(fill="x", padx=30, pady=(0, 15))

        self.e_password = ctk.CTkEntry(
            card,
            placeholder_text="Contraseña",
            show="*",  # Ocultar texto
            font=s.f_normal(),
            height=s.BTN_HEIGHT,
            corner_radius=s.CORNER,
        )
        self.e_password.pack(fill="x", padx=30, pady=(0, 25))

        # Permitir presionar "Enter" para iniciar sesión
        self.e_password.bind("<Return>", lambda e: self.iniciar_sesion())

        # Botón Login
        btn_login = ctk.CTkButton(
            card,
            text="Iniciar Sesión",
            fg_color=s.C_BLUE,
            hover_color=s.hover(s.C_BLUE),
            font=s.f_bold(),
            height=s.BTN_HEIGHT_LG,
            corner_radius=s.CORNER,
            command=self.iniciar_sesion,
        )
        btn_login.pack(fill="x", padx=30, pady=(0, 20))

    def iniciar_sesion(self):
        usuario = self.e_usuario.get().strip()
        pwd = self.e_password.get().strip()

        if not usuario or not pwd:
            messagebox.showwarning(
                "Atención", "Por favor ingresa usuario y contraseña."
            )
            return

        try:
            datos_usuario = db.verificar_login(usuario, pwd)

            if datos_usuario:
                # Opcional: Mostrar mensaje de bienvenida
                # messagebox.showinfo("Éxito", f"Bienvenido, {datos_usuario['username']}")

                # Destruimos la ventana de login
                self.destroy()

                # Iniciamos la aplicación principal
                app = App()
                # Si quieres que tu main.py sepa quién inició sesión, podrías guardarlo:
                # app.usuario_actual = datos_usuario
                app.mainloop()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))


if __name__ == "__main__":
    login = LoginWindow()
    login.mainloop()
