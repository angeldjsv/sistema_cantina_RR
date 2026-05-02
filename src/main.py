import customtkinter as ctk
from PIL import Image # La usaremos más adelante para iconos
from tkinter import ttk

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
    def limpiar_panel_derecho(self):
        for widget in self.home_frame.winfo_children():
            widget.destroy()

    def pos_button_event(self):
        print("Cambiando a Punto de Venta...")

    def cuentas_button_event(self):
        print("Cambiando a Gestión de Cuentas...")

    def productos_button_event(self):
        self.limpiar_panel_derecho()

        # Título del módulo
        titulo = ctk.CTkLabel(
            self.home_frame, text="Gestión de Menú y Productos", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        titulo.pack(pady=20)

        # Marco para el formulario (Cajas de texto)
        frame_formulario = ctk.CTkFrame(self.home_frame)
        frame_formulario.pack(pady=10, padx=20, fill="x")

        # Cajas de entrada de datos
        self.entry_nombre_prod = ctk.CTkEntry(frame_formulario, placeholder_text="Nombre del Producto", width=200)
        self.entry_nombre_prod.grid(row=0, column=0, padx=10, pady=10)

        self.menu_categoria = ctk.CTkOptionMenu(frame_formulario, values=["Desayuno", "Bebida", "Chuchería"])
        self.menu_categoria.grid(row=0, column=1, padx=10, pady=10)

        self.entry_precio_prod = ctk.CTkEntry(frame_formulario, placeholder_text="Precio (Ej: 1.50)", width=100)
        self.entry_precio_prod.grid(row=0, column=2, padx=10, pady=10)

        # Botón Guardar (Por ahora solo imprime en consola, luego lo conectaremos a MySQL)
        btn_guardar_prod = ctk.CTkButton(
            frame_formulario, text="Guardar Producto", fg_color="green", hover_color="darkgreen",
            command=self.guardar_producto_db
        )
        btn_guardar_prod.grid(row=0, column=3, padx=10, pady=10)

        # Configurar la tabla para mostrar los productos
        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure("Treeview", background="#2a2d2e", foreground="white", rowheight=25, fieldbackground="#343638")
        estilo.map('Treeview', background=[('selected', '#22559b')])

        self.tabla_productos = ttk.Treeview(self.home_frame, columns=("ID", "Nombre", "Categoría", "Precio"), show="headings")
        self.tabla_productos.heading("ID", text="ID")
        self.tabla_productos.heading("Nombre", text="Nombre")
        self.tabla_productos.heading("Categoría", text="Categoría")
        self.tabla_productos.heading("Precio", text="Precio ($)")
        
        self.tabla_productos.column("ID", width=50, anchor="center")
        self.tabla_productos.column("Precio", width=100, anchor="center")
        
        self.tabla_productos.pack(pady=20, padx=20, fill="both", expand=True)

    # Función temporal para el botón Guardar
    def guardar_producto_db(self):
        print(f"Guardando: {self.entry_nombre_prod.get()} - {self.menu_categoria.get()} - {self.entry_precio_prod.get()}$")

    def change_appearance_mode_event(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = App()
    app.mainloop()