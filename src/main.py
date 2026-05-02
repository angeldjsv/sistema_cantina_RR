import customtkinter as ctk
from PIL import Image # La usaremos más adelante para iconos

# Configuración estética global
ctk.set_appearance_mode("dark")  # Modos: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Temas: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Sistema de Gestión Cantina R.R.")
        self.geometry("1000x600")

        # Configurar el diseño de cuadrícula (Grid) 1x2
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- NAVEGACIÓN LATERAL (BARRA IZQUIERDA) ---
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.navigation_frame_label = ctk.CTkLabel(
            self.navigation_frame, text="  CANTINA R.R.", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        # Botones de navegación
        self.btn_pos = ctk.CTkButton(
            self.navigation_frame, corner_radius=0, height=40, border_spacing=10, 
            text="Punto de Venta", fg_color="transparent", text_color=("gray10", "gray90"), 
            hover_color=("gray70", "gray30"), anchor="w", command=self.pos_button_event
        )
        self.btn_pos.grid(row=1, column=0, sticky="ew")

        self.btn_cuentas = ctk.CTkButton(
            self.navigation_frame, corner_radius=0, height=40, border_spacing=10, 
            text="Gestión de Cuentas", fg_color="transparent", text_color=("gray10", "gray90"), 
            hover_color=("gray70", "gray30"), anchor="w", command=self.cuentas_button_event
        )
        self.btn_cuentas.grid(row=2, column=0, sticky="ew")

        self.btn_productos = ctk.CTkButton(
            self.navigation_frame, corner_radius=0, height=40, border_spacing=10, 
            text="Menú / Productos", fg_color="transparent", text_color=("gray10", "gray90"), 
            hover_color=("gray70", "gray30"), anchor="w", command=self.productos_button_event
        )
        self.btn_productos.grid(row=3, column=0, sticky="ew")

        # Selector de Modo (Oscuro/Claro) al final de la barra
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.navigation_frame, values=["Dark", "Light", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # --- CONTENIDO PRINCIPAL (DERECHA) ---
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid(row=0, column=1, sticky="nsew")
        
        self.main_label = ctk.CTkLabel(
            self.home_frame, text="Bienvenido al Sistema de Gestión", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.main_label.pack(pady=40)

    # --- FUNCIONES DE LOS EVENTOS ---
    def pos_button_event(self):
        print("Cambiando a Punto de Venta...")

    def cuentas_button_event(self):
        print("Cambiando a Gestión de Cuentas...")

    def productos_button_event(self):
        print("Cambiando a Menú de Productos...")

    def change_appearance_mode_event(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = App()
    app.mainloop()