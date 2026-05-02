import customtkinter as ctk
from PIL import Image # La usaremos más adelante para iconos
from tkinter import ttk
from conexion import conectar
from tkinter import messagebox # Para mostrar alertas de "Guardado con éxito"

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
        self.limpiar_panel_derecho()

        # Título
        titulo = ctk.CTkLabel(self.home_frame, text="Gestión de Cuentas y Familias", font=ctk.CTkFont(size=24, weight="bold"))
        titulo.pack(pady=20)

        # --- FORMULARIO DE CUENTA ---
        frame_form_cuenta = ctk.CTkFrame(self.home_frame)
        frame_form_cuenta.pack(pady=10, padx=20, fill="x")

        self.entry_ref_cuenta = ctk.CTkEntry(frame_form_cuenta, placeholder_text="Nombre Ref (Ej: Familia Perez)", width=250)
        self.entry_ref_cuenta.grid(row=0, column=0, padx=10, pady=10)

        self.entry_tel_cuenta = ctk.CTkEntry(frame_form_cuenta, placeholder_text="Teléfono", width=150)
        self.entry_tel_cuenta.grid(row=0, column=1, padx=10, pady=10)

        self.menu_tipo_usuario = ctk.CTkOptionMenu(frame_form_cuenta, values=["Estudiante", "Docente", "Obrero", "Administrativo"])
        self.menu_tipo_usuario.grid(row=0, column=2, padx=10, pady=10)

        btn_guardar_cuenta = ctk.CTkButton(frame_form_cuenta, text="Crear Cuenta", fg_color="green", command=self.guardar_cuenta_db)
        btn_guardar_cuenta.grid(row=0, column=3, padx=10, pady=10)

        # --- TABLA DE CUENTAS (Principal) ---
        self.tabla_cuentas = ttk.Treeview(self.home_frame, columns=("ID", "Referencia", "Teléfono", "Tipo", "Deuda", "A Favor"), show="headings")
        self.tabla_cuentas.heading("ID", text="ID")
        self.tabla_cuentas.heading("Referencia", text="Referencia")
        self.tabla_cuentas.heading("Teléfono", text="Teléfono")
        self.tabla_cuentas.heading("Tipo", text="Tipo")
        self.tabla_cuentas.heading("Deuda", text="Saldo Deuda ($)")
        self.tabla_cuentas.heading("A Favor", text="Saldo Favor ($)")
        
        # Ajustar anchos
        self.tabla_cuentas.column("ID", width=50)
        self.tabla_cuentas.column("Referencia", width=200)
        
        self.tabla_cuentas.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.cargar_cuentas()

        # --- 1. DISPARADOR DE SELECCIÓN ---
        # Esto avisa al sistema cuando haces clic en una fila de la tabla superior
        self.tabla_cuentas.bind("<<TreeviewSelect>>", self.on_cuenta_select)

        # --- 2. TABLA SECUNDARIA (Estudiantes Asociados) ---
        ctk.CTkLabel(self.home_frame, text="Estudiantes vinculados a la cuenta seleccionada:", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))

        self.tabla_estudiantes_asociados = ttk.Treeview(
            self.home_frame, 
            columns=("Nombre", "Apellido", "Grado"), 
            show="headings", 
            height=4 # Altura reducida para que quepa bien en la pantalla
        )
        self.tabla_estudiantes_asociados.heading("Nombre", text="Nombre")
        self.tabla_estudiantes_asociados.heading("Apellido", text="Apellido")
        self.tabla_estudiantes_asociados.heading("Grado", text="Grado")
        
        self.tabla_estudiantes_asociados.pack(pady=10, padx=20, fill="x")

        # --- 3. BOTÓN MOVIDO AL FINAL ---
        btn_agregar_est = ctk.CTkButton(
            self.home_frame, 
            text="➕ Vincular Nuevo Estudiante", 
            fg_color="#1f538d", 
            command=self.abrir_ventana_estudiante
        )
        btn_agregar_est.pack(pady=(0, 10))

    def abrir_ventana_estudiante(self):
        # 1. Verificar si hay una cuenta seleccionada en la tabla
        seleccion = self.tabla_cuentas.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debes hacer clic en una cuenta de la tabla primero.")
            return
        
        # 2. Extraer los datos de la fila seleccionada
        item = self.tabla_cuentas.item(seleccion[0])
        id_cuenta = item['values'][0]
        nombre_cuenta = item['values'][1]
        tipo_cuenta = item['values'][3]

        # Si es un docente u obrero, no le asociamos niños
        if tipo_cuenta != "Estudiante":
            messagebox.showinfo("Aviso", "Esta cuenta pertenece a Personal. No requiere asociar estudiantes.")
            return

        # 3. Crear la ventana emergente
        ventana_est = ctk.CTkToplevel(self)
        ventana_est.title(f"Añadir a: {nombre_cuenta}")
        ventana_est.geometry("400x400")
        ventana_est.grab_set() # Hace que no puedas tocar la ventana de atrás hasta cerrar esta

        ctk.CTkLabel(ventana_est, text="Nombre del Estudiante:", font=("Arial", 14)).pack(pady=(20, 5))
        entry_nom = ctk.CTkEntry(ventana_est, width=250)
        entry_nom.pack(pady=5)

        ctk.CTkLabel(ventana_est, text="Apellido del Estudiante:", font=("Arial", 14)).pack(pady=5)
        entry_ape = ctk.CTkEntry(ventana_est, width=250)
        entry_ape.pack(pady=5)

        ctk.CTkLabel(ventana_est, text="Grado y Sección:", font=("Arial", 14)).pack(pady=5)
        entry_grado = ctk.CTkEntry(ventana_est, width=250, placeholder_text="Ej: 5to A")
        entry_grado.pack(pady=5)

        # 4. Botón que dispara el guardado en base de datos
        btn_guardar = ctk.CTkButton(
            ventana_est, text="Guardar Estudiante", fg_color="green", 
            command=lambda: self.guardar_estudiante_db(id_cuenta, entry_nom.get(), entry_ape.get(), entry_grado.get(), ventana_est)
        )
        btn_guardar.pack(pady=30)

    def guardar_estudiante_db(self, id_cuenta, nombre, apellido, grado, ventana):
        if not nombre or not apellido or not grado:
            messagebox.showwarning("Atención", "Todos los campos son obligatorios.")
            return
        
        con = conectar()
        if con:
            try:
                cursor = con.cursor()
                # OJO: Tu tabla usa la columna "grado", asegúrate que coincida.
                sql = "INSERT INTO estudiantes (nombre, apellido, grado, id_cuenta) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (nombre, apellido, grado, id_cuenta))
                con.commit()
                con.close()
                
                messagebox.showinfo("Éxito", f"Estudiante {nombre} {apellido} asignado correctamente.")
                self.cargar_estudiantes_asociados(id_cuenta) # Refrescar la lista de niños
                ventana.destroy() # Cierra la ventanita emergente
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error en la base de datos: {e}")

    # --- LÓGICA DE BASE DE DATOS PARA CUENTAS ---
    def guardar_cuenta_db(self):
        ref = self.entry_ref_cuenta.get()
        tel = self.entry_tel_cuenta.get()
        tipo = self.menu_tipo_usuario.get()

        if not ref or not tel:
            messagebox.showwarning("Atención", "Nombre de referencia y teléfono son obligatorios")
            return

        con = conectar()
        if con:
            try:
                cursor = con.cursor()
                sql = "INSERT INTO cuentas (nombre_referencia, telefono, tipo_usuario) VALUES (%s, %s, %s)"
                cursor.execute(sql, (ref, tel, tipo))
                con.commit()
                con.close()
                messagebox.showinfo("Éxito", f"Cuenta '{ref}' creada.")
                self.entry_ref_cuenta.delete(0, 'end')
                self.entry_tel_cuenta.delete(0, 'end')
                self.cargar_cuentas()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear cuenta: {e}")

    def cargar_cuentas(self):
        for item in self.tabla_cuentas.get_children():
            self.tabla_cuentas.delete(item)
        con = conectar()
        if con:
            cursor = con.cursor()
            cursor.execute("SELECT id_cuenta, nombre_referencia, telefono, tipo_usuario, saldo_deuda, saldo_favor FROM cuentas")
            for fila in cursor.fetchall():
                self.tabla_cuentas.insert("", "end", values=fila)
            con.close()

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
        self.cargar_productos() # Carga los datos apenas entras al módulo

    # Función temporal para el botón Guardar
    def guardar_producto_db(self):
        nombre = self.entry_nombre_prod.get()
        cat = self.menu_categoria.get()
        precio = self.entry_precio_prod.get()

        if not nombre or not precio:
            messagebox.showwarning("Atención", "Todos los campos son obligatorios")
            return

        con = conectar()
        if con:
            try:
                cursor = con.cursor()
                sql = "INSERT INTO productos (nombre, categoria, precio) VALUES (%s, %s, %s)"
                valores = (nombre, cat, precio)
                cursor.execute(sql, valores)
                con.commit() # ¡Importante para guardar cambios!
                con.close()
                
                messagebox.showinfo("Éxito", f"Producto '{nombre}' guardado correctamente")
                
                # Limpiar cajas de texto
                self.entry_nombre_prod.delete(0, 'end')
                self.entry_precio_prod.delete(0, 'end')
                
                # Refrescar la tabla para ver el cambio
                self.cargar_productos()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def change_appearance_mode_event(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def cargar_productos(self):
        # Limpiar tabla primero
        for item in self.tabla_productos.get_children():
            self.tabla_productos.delete(item)
            
        con = conectar()
        if con:
            cursor = con.cursor()
            cursor.execute("SELECT id_producto, nombre, categoria, precio FROM productos")
            for fila in cursor.fetchall():
                self.tabla_productos.insert("", "end", values=fila)
            con.close()

    def on_cuenta_select(self, event):
        """Se activa cada vez que el usuario hace clic en una cuenta de la tabla"""
        seleccion = self.tabla_cuentas.selection()
        if seleccion:
            item = self.tabla_cuentas.item(seleccion[0])
            id_cuenta = item['values'][0] # Obtenemos el ID de la cuenta
            self.cargar_estudiantes_asociados(id_cuenta)

    def cargar_estudiantes_asociados(self, id_cuenta):
        """Busca en MySQL los niños que pertenecen a ese ID de cuenta"""
        # Limpiar tabla de estudiantes primero
        for item in self.tabla_estudiantes_asociados.get_children():
            self.tabla_estudiantes_asociados.delete(item)
            
        con = conectar()
        if con:
            cursor = con.cursor()
            query = "SELECT nombre, apellido, grado FROM estudiantes WHERE id_cuenta = %s"
            cursor.execute(query, (id_cuenta,))
            
            for fila in cursor.fetchall():
                self.tabla_estudiantes_asociados.insert("", "end", values=fila)
            con.close()
if __name__ == "__main__":
    app = App()
    app.mainloop()