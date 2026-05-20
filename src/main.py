import customtkinter as ctk
from tkinter import ttk, messagebox
from conexion import conectar

# ============================================================
# CONFIGURACIÓN ESTÉTICA GLOBAL
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================
# CLASE PRINCIPAL
# ============================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema de Gestión - Cantina R.R.")
        self.geometry("1100x650")

        # Tasa BCV activa (se carga al iniciar)
        self.tasa_bcv = self.obtener_tasa_bcv()

        # Carrito de compras (lista de dicts)
        self.carrito = []

        # Grid principal: columna 0 = nav, columna 1 = contenido
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── BARRA DE NAVEGACIÓN LATERAL ──────────────────────
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            self.navigation_frame, text="  CANTINA R.R.",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=20)

        # Tasa BCV en la barra lateral
        self.label_tasa_nav = ctk.CTkLabel(
            self.navigation_frame,
            text=f"Tasa BCV:\nBs. {self.tasa_bcv:,.2f}",
            font=ctk.CTkFont(size=12),
            text_color="lightgreen"
        )
        self.label_tasa_nav.grid(row=1, column=0, padx=20, pady=(0, 10))

        nav_buttons = [
            ("🛒  Punto de Venta",       self.pos_button_event,       2),
            ("👥  Gestión de Cuentas",   self.cuentas_button_event,   3),
            ("🍔  Menú / Productos",     self.productos_button_event, 4),
        ]
        for texto, comando, fila in nav_buttons:
            ctk.CTkButton(
                self.navigation_frame, corner_radius=0, height=40,
                border_spacing=10, text=texto, fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                anchor="w", command=comando
            ).grid(row=fila, column=0, sticky="ew")

        self.appearance_mode_menu = ctk.CTkOptionMenu(
            self.navigation_frame, values=["Dark", "Light", "System"],
            command=lambda m: ctk.set_appearance_mode(m)
        )
        self.appearance_mode_menu.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        # ── PANEL DE CONTENIDO PRINCIPAL ─────────────────────
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid(row=0, column=1, sticky="nsew")

        # Pantalla de bienvenida
        ctk.CTkLabel(
            self.home_frame,
            text="Bienvenido al Sistema de Gestión\nCantina Escolar R.R.",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=80)
        ctk.CTkLabel(
            self.home_frame,
            text=f"Tasa BCV activa: Bs. {self.tasa_bcv:,.2f}",
            font=ctk.CTkFont(size=14),
            text_color="lightgreen"
        ).pack()

    # ============================================================
    # UTILIDADES GENERALES
    # ============================================================
    def limpiar_panel_derecho(self):
        for widget in self.home_frame.winfo_children():
            widget.destroy()
        # Resetear configuración de grid del panel
        self.home_frame.grid_columnconfigure(0, weight=0)
        self.home_frame.grid_columnconfigure(1, weight=0)

    def obtener_tasa_bcv(self):
        """Obtiene la tasa BCV más reciente guardada en la base de datos."""
        con = conectar()
        if con:
            try:
                cursor = con.cursor()
                cursor.execute("SELECT tasa FROM tasa_bcv ORDER BY fecha DESC LIMIT 1")
                resultado = cursor.fetchone()
                con.close()
                if resultado:
                    return float(resultado[0])
            except Exception:
                pass
        return 1.0  # Valor de seguridad si no hay conexión

    # ============================================================
    # MÓDULO: PUNTO DE VENTA (POS)
    # ============================================================
    def pos_button_event(self):
        self.limpiar_panel_derecho()
        self.carrito = []

        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_columnconfigure(1, weight=0)
        self.home_frame.grid_rowconfigure(0, weight=1)

        # ── COLUMNA IZQUIERDA: PRODUCTOS ─────────────────────
        frame_productos = ctk.CTkFrame(self.home_frame)
        frame_productos.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_productos.grid_rowconfigure(2, weight=1)
        frame_productos.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_productos, text="Productos Disponibles",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=10)

        # Buscador
        self.entry_buscar_pos = ctk.CTkEntry(
            frame_productos, placeholder_text="🔍 Buscar producto...", width=320
        )
        self.entry_buscar_pos.grid(row=1, column=0, pady=5, padx=10)
        self.entry_buscar_pos.bind("<KeyRelease>", self.filtrar_productos_pos)

        # Tabla productos
        cols_prod = ("ID", "Producto", "Precio $", "Precio Bs.")
        self.tabla_pos_prod = ttk.Treeview(
            frame_productos, columns=cols_prod, show="headings", height=16
        )
        for col in cols_prod:
            self.tabla_pos_prod.heading(col, text=col)
        self.tabla_pos_prod.column("ID",         width=40,  anchor="center")
        self.tabla_pos_prod.column("Producto",   width=200)
        self.tabla_pos_prod.column("Precio $",   width=80,  anchor="center")
        self.tabla_pos_prod.column("Precio Bs.", width=100, anchor="center")
        self.tabla_pos_prod.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # Doble clic para añadir al carrito
        self.tabla_pos_prod.bind("<Double-1>", self.añadir_al_carrito)

        ctk.CTkButton(
            frame_productos, text="🛒  Añadir al Carrito  (o doble clic)",
            fg_color="#1f538d", command=self.añadir_al_carrito
        ).grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        # ── COLUMNA DERECHA: CARRITO Y COBRO ─────────────────
        frame_carrito = ctk.CTkFrame(self.home_frame, width=370, fg_color=("#dbdbdb", "#2b2b2b"))
        frame_carrito.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_carrito.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_carrito, text="Carrito de Compras",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        cols_cart = ("Producto", "Cant.", "Subtotal $")
        self.tabla_carrito = ttk.Treeview(
            frame_carrito, columns=cols_cart, show="headings", height=12
        )
        for col in cols_cart:
            self.tabla_carrito.heading(col, text=col)
        self.tabla_carrito.column("Producto",    width=160)
        self.tabla_carrito.column("Cant.",       width=50,  anchor="center")
        self.tabla_carrito.column("Subtotal $",  width=90,  anchor="center")
        self.tabla_carrito.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        ctk.CTkButton(
            frame_carrito, text="🗑️  Quitar seleccionado",
            fg_color="#7f0000", width=160, command=self.quitar_del_carrito
        ).grid(row=2, column=0, padx=5, pady=5)

        ctk.CTkButton(
            frame_carrito, text="🧹  Vaciar carrito",
            fg_color="#555", width=160, command=self.vaciar_carrito
        ).grid(row=2, column=1, padx=5, pady=5)

        # Totales
        self.label_total_usd = ctk.CTkLabel(
            frame_carrito, text="TOTAL: $0.00",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="lightgreen"
        )
        self.label_total_usd.grid(row=3, column=0, columnspan=2, pady=(15, 2))

        self.label_total_bs = ctk.CTkLabel(
            frame_carrito, text="Bs. 0,00",
            font=ctk.CTkFont(size=14), text_color="lightyellow"
        )
        self.label_total_bs.grid(row=4, column=0, columnspan=2, pady=(0, 10))

        # Cuenta
        ctk.CTkLabel(frame_carrito, text="Asignar a cuenta:").grid(
            row=5, column=0, columnspan=2
        )
        self.combo_cuentas_pos = ctk.CTkOptionMenu(
            frame_carrito, values=["Seleccionar cuenta..."], width=320
        )
        self.combo_cuentas_pos.grid(row=6, column=0, columnspan=2, pady=8, padx=10)

        # Método de pago
        ctk.CTkLabel(frame_carrito, text="Método de pago:").grid(
            row=7, column=0, columnspan=2
        )
        self.combo_metodo_pago = ctk.CTkOptionMenu(
            frame_carrito,
            values=["Efectivo", "Pago Móvil", "Transferencia", "Pendiente"],
            width=320
        )
        self.combo_metodo_pago.grid(row=8, column=0, columnspan=2, pady=8, padx=10)

        ctk.CTkButton(
            frame_carrito, text="✅  FINALIZAR VENTA",
            fg_color="green", height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.finalizar_venta
        ).grid(row=9, column=0, columnspan=2, pady=15, padx=20, sticky="ew")

        self.cargar_productos_pos()
        self.cargar_cuentas_combo()

    def cargar_productos_pos(self, filtro=""):
        for item in self.tabla_pos_prod.get_children():
            self.tabla_pos_prod.delete(item)
        con = conectar()
        if con:
            cursor = con.cursor()
            if filtro:
                cursor.execute(
                    "SELECT id_producto, nombre, precio_usd FROM productos "
                    "WHERE estado='Disponible' AND nombre LIKE %s ORDER BY categoria, nombre",
                    (f"%{filtro}%",)
                )
            else:
                cursor.execute(
                    "SELECT id_producto, nombre, precio_usd FROM productos "
                    "WHERE estado='Disponible' ORDER BY categoria, nombre"
                )
            for fila in cursor.fetchall():
                precio_usd = float(fila[2])
                precio_bs  = precio_usd * self.tasa_bcv
                self.tabla_pos_prod.insert("", "end", values=(
                    fila[0], fila[1],
                    f"${precio_usd:.2f}",
                    f"Bs. {precio_bs:,.2f}"
                ))
            con.close()

    def filtrar_productos_pos(self, event=None):
        self.cargar_productos_pos(filtro=self.entry_buscar_pos.get())

    def añadir_al_carrito(self, event=None):
        seleccion = self.tabla_pos_prod.selection()
        if not seleccion:
            return
        item = self.tabla_pos_prod.item(seleccion[0])
        id_prod, nombre, precio_str, _ = item["values"]
        precio_usd = float(precio_str.replace("$", ""))

        # Si ya está en el carrito, aumentar cantidad
        for prod in self.carrito:
            if prod["id"] == id_prod:
                prod["cantidad"] += 1
                prod["subtotal"] = round(prod["cantidad"] * prod["precio"], 2)
                self.actualizar_tabla_carrito()
                return

        self.carrito.append({
            "id": id_prod, "nombre": nombre,
            "precio": precio_usd, "cantidad": 1,
            "subtotal": precio_usd
        })
        self.actualizar_tabla_carrito()

    def quitar_del_carrito(self):
        seleccion = self.tabla_carrito.selection()
        if not seleccion:
            return
        idx = self.tabla_carrito.index(seleccion[0])
        del self.carrito[idx]
        self.actualizar_tabla_carrito()

    def vaciar_carrito(self):
        self.carrito = []
        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
        total_usd = 0.0
        for prod in self.carrito:
            self.tabla_carrito.insert("", "end", values=(
                prod["nombre"], prod["cantidad"], f"${prod['subtotal']:.2f}"
            ))
            total_usd += prod["subtotal"]
        total_bs = total_usd * self.tasa_bcv
        self.label_total_usd.configure(text=f"TOTAL: ${total_usd:.2f}")
        self.label_total_bs.configure(text=f"Bs. {total_bs:,.2f}")

    def cargar_cuentas_combo(self):
        con = conectar()
        if con:
            cursor = con.cursor()
            cursor.execute("SELECT id_cuenta, nombre_referencia FROM cuentas ORDER BY nombre_referencia")
            filas = cursor.fetchall()
            con.close()
            if filas:
                self.cuentas_map = {f"{f[1]} (ID:{f[0]})": f[0] for f in filas}
                self.combo_cuentas_pos.configure(values=list(self.cuentas_map.keys()))
                self.combo_cuentas_pos.set(list(self.cuentas_map.keys())[0])
            else:
                self.cuentas_map = {}
                self.combo_cuentas_pos.configure(values=["Sin cuentas registradas"])

    def finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito vacío", "Agrega productos antes de finalizar.")
            return

        cuenta_sel = self.combo_cuentas_pos.get()
        if "ID:" not in cuenta_sel:
            messagebox.showwarning("Sin cuenta", "Selecciona una cuenta válida.")
            return

        id_cuenta   = self.cuentas_map[cuenta_sel]
        metodo      = self.combo_metodo_pago.get()
        total_usd   = sum(p["subtotal"] for p in self.carrito)
        total_bs    = round(total_usd * self.tasa_bcv, 2)

        con = conectar()
        if con:
            try:
                cursor = con.cursor()

                # 1. Insertar transacción
                cursor.execute(
                    "INSERT INTO transacciones "
                    "(id_cuenta, tipo, monto_total_usd, monto_total_bs, tasa_aplicada, metodo_pago) "
                    "VALUES (%s, 'Consumo', %s, %s, %s, %s)",
                    (id_cuenta, total_usd, total_bs, self.tasa_bcv, metodo)
                )
                id_trans = cursor.lastrowid

                # 2. Insertar detalles
                for prod in self.carrito:
                    cursor.execute(
                        "INSERT INTO detalles_transaccion "
                        "(id_transaccion, id_producto, cantidad, precio_unitario_usd, subtotal_usd) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (id_trans, prod["id"], prod["cantidad"], prod["precio"], prod["subtotal"])
                    )

                # 3. Actualizar saldo de la cuenta
                if metodo == "Pendiente":
                    cursor.execute(
                        "UPDATE cuentas SET saldo_deuda = saldo_deuda + %s WHERE id_cuenta = %s",
                        (total_usd, id_cuenta)
                    )
                else:
                    cursor.execute(
                        "UPDATE cuentas SET saldo_favor = saldo_favor + %s WHERE id_cuenta = %s",
                        (total_usd, id_cuenta)
                    )

                con.commit()
                con.close()

                messagebox.showinfo(
                    "Venta Registrada ✅",
                    f"Venta finalizada correctamente.\n\n"
                    f"Total: ${total_usd:.2f} / Bs. {total_bs:,.2f}\n"
                    f"Método: {metodo}\n"
                    f"Cuenta: {cuenta_sel}"
                )
                self.vaciar_carrito()

            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar la venta:\n{e}")

    # ============================================================
    # MÓDULO: GESTIÓN DE CUENTAS
    # ============================================================
    def cuentas_button_event(self):
        self.limpiar_panel_derecho()

        ctk.CTkLabel(
            self.home_frame, text="Gestión de Cuentas y Personas",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        # Formulario nueva cuenta
        frame_form = ctk.CTkFrame(self.home_frame)
        frame_form.pack(pady=5, padx=20, fill="x")

        self.entry_ref_cuenta = ctk.CTkEntry(
            frame_form, placeholder_text="Nombre Ref. (Ej: Familia Pérez)", width=250
        )
        self.entry_ref_cuenta.grid(row=0, column=0, padx=10, pady=10)

        self.entry_tel_cuenta = ctk.CTkEntry(
            frame_form, placeholder_text="Teléfono", width=160
        )
        self.entry_tel_cuenta.grid(row=0, column=1, padx=10, pady=10)

        self.menu_tipo_usuario = ctk.CTkOptionMenu(
            frame_form, values=["Estudiante", "Docente", "Obrero", "Administrativo"]
        )
        self.menu_tipo_usuario.grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkButton(
            frame_form, text="➕ Crear Cuenta", fg_color="green",
            command=self.guardar_cuenta_db
        ).grid(row=0, column=3, padx=10, pady=10)

        # Tabla de cuentas
        self.tabla_cuentas = ttk.Treeview(
            self.home_frame,
            columns=("ID", "Referencia", "Teléfono", "Tipo", "Deuda $", "A Favor $"),
            show="headings"
        )
        for col in ("ID", "Referencia", "Teléfono", "Tipo", "Deuda $", "A Favor $"):
            self.tabla_cuentas.heading(col, text=col)
        self.tabla_cuentas.column("ID",        width=40,  anchor="center")
        self.tabla_cuentas.column("Referencia",width=200)
        self.tabla_cuentas.column("Teléfono",  width=130)
        self.tabla_cuentas.column("Tipo",      width=110, anchor="center")
        self.tabla_cuentas.column("Deuda $",   width=90,  anchor="center")
        self.tabla_cuentas.column("A Favor $", width=90,  anchor="center")
        self.tabla_cuentas.pack(pady=5, padx=20, fill="both", expand=True)
        self.tabla_cuentas.bind("<<TreeviewSelect>>", self.on_cuenta_select)

        self.cargar_cuentas()

        # Tabla personas asociadas
        ctk.CTkLabel(
            self.home_frame,
            text="Personas vinculadas a la cuenta seleccionada:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(8, 0))

        self.tabla_personas_asociadas = ttk.Treeview(
            self.home_frame,
            columns=("Nombre", "Apellido", "Tipo", "Grado/Sección"),
            show="headings", height=4
        )
        for col in ("Nombre", "Apellido", "Tipo", "Grado/Sección"):
            self.tabla_personas_asociadas.heading(col, text=col)
        self.tabla_personas_asociadas.pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(
            self.home_frame, text="➕ Vincular Persona a esta Cuenta",
            fg_color="#1f538d", command=self.abrir_ventana_persona
        ).pack(pady=(0, 10))

    def guardar_cuenta_db(self):
        ref  = self.entry_ref_cuenta.get().strip()
        tel  = self.entry_tel_cuenta.get().strip()
        tipo = self.menu_tipo_usuario.get()

        if not ref or not tel:
            messagebox.showwarning("Atención", "Nombre de referencia y teléfono son obligatorios.")
            return

        con = conectar()
        if con:
            try:
                cursor = con.cursor()
                cursor.execute(
                    "INSERT INTO cuentas (nombre_referencia, telefono, tipo_usuario) VALUES (%s, %s, %s)",
                    (ref, tel, tipo)
                )
                con.commit()
                con.close()
                messagebox.showinfo("Éxito", f"Cuenta '{ref}' creada correctamente.")
                self.entry_ref_cuenta.delete(0, "end")
                self.entry_tel_cuenta.delete(0, "end")
                self.cargar_cuentas()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la cuenta:\n{e}")

    def cargar_cuentas(self):
        for item in self.tabla_cuentas.get_children():
            self.tabla_cuentas.delete(item)
        con = conectar()
        if con:
            cursor = con.cursor()
            cursor.execute(
                "SELECT id_cuenta, nombre_referencia, telefono, tipo_usuario, "
                "saldo_deuda, saldo_favor FROM cuentas ORDER BY nombre_referencia"
            )
            for fila in cursor.fetchall():
                self.tabla_cuentas.insert("", "end", values=fila)
            con.close()

    def on_cuenta_select(self, event=None):
        seleccion = self.tabla_cuentas.selection()
        if seleccion:
            id_cuenta = self.tabla_cuentas.item(seleccion[0])["values"][0]
            self.cargar_personas_asociadas(id_cuenta)

    def cargar_personas_asociadas(self, id_cuenta):
        for item in self.tabla_personas_asociadas.get_children():
            self.tabla_personas_asociadas.delete(item)
        con = conectar()
        if con:
            cursor = con.cursor()
            cursor.execute(
                "SELECT nombre, apellido, tipo, grado_seccion FROM personas WHERE id_cuenta = %s",
                (id_cuenta,)
            )
            for fila in cursor.fetchall():
                self.tabla_personas_asociadas.insert("", "end", values=fila)
            con.close()

    def abrir_ventana_persona(self):
        seleccion = self.tabla_cuentas.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona primero una cuenta de la tabla.")
            return

        item       = self.tabla_cuentas.item(seleccion[0])
        id_cuenta  = item["values"][0]
        nom_cuenta = item["values"][1]

        ventana = ctk.CTkToplevel(self)
        ventana.title(f"Vincular persona a: {nom_cuenta}")
        ventana.geometry("420x420")
        ventana.grab_set()

        campos = [
            ("Nombre:",         "entry_pnombre",  None),
            ("Apellido:",       "entry_papellido", None),
            ("Grado/Sección:",  "entry_pgrado",   "Ej: 5to A  (dejar vacío si no aplica)"),
        ]
        entries = {}
        for label, key, ph in campos:
            ctk.CTkLabel(ventana, text=label, font=("Arial", 13)).pack(pady=(12, 2))
            e = ctk.CTkEntry(ventana, width=280, placeholder_text=ph or "")
            e.pack()
            entries[key] = e

        ctk.CTkLabel(ventana, text="Tipo:", font=("Arial", 13)).pack(pady=(12, 2))
        menu_tipo = ctk.CTkOptionMenu(
            ventana, values=["Estudiante", "Docente", "Obrero", "Administrativo"], width=280
        )
        menu_tipo.pack()

        ctk.CTkButton(
            ventana, text="💾 Guardar", fg_color="green", width=200,
            command=lambda: self.guardar_persona_db(
                id_cuenta,
                entries["entry_pnombre"].get(),
                entries["entry_papellido"].get(),
                entries["entry_pgrado"].get(),
                menu_tipo.get(),
                ventana
            )
        ).pack(pady=25)

    def guardar_persona_db(self, id_cuenta, nombre, apellido, grado, tipo, ventana):
        if not nombre.strip() or not apellido.strip():
            messagebox.showwarning("Atención", "Nombre y apellido son obligatorios.")
            return
        con = conectar()
        if con:
            try:
                cursor = con.cursor()
                cursor.execute(
                    "INSERT INTO personas (nombre, apellido, tipo, grado_seccion, id_cuenta) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (nombre.strip(), apellido.strip(), tipo, grado.strip() or None, id_cuenta)
                )
                con.commit()
                con.close()
                messagebox.showinfo("Éxito", f"{nombre} {apellido} vinculado correctamente.")
                self.cargar_personas_asociadas(id_cuenta)
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    # ============================================================
    # MÓDULO: GESTIÓN DE PRODUCTOS
    # ============================================================
    def productos_button_event(self):
        self.limpiar_panel_derecho()

        ctk.CTkLabel(
            self.home_frame, text="Gestión de Menú y Productos",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        frame_form = ctk.CTkFrame(self.home_frame)
        frame_form.pack(pady=5, padx=20, fill="x")

        self.entry_nombre_prod = ctk.CTkEntry(
            frame_form, placeholder_text="Nombre del Producto", width=200
        )
        self.entry_nombre_prod.grid(row=0, column=0, padx=10, pady=10)

        self.menu_categoria = ctk.CTkOptionMenu(
            frame_form, values=["Por Unidad", "Combos", "Bebidas", "Meriendas"]
        )
        self.menu_categoria.grid(row=0, column=1, padx=10, pady=10)

        self.entry_precio_prod = ctk.CTkEntry(
            frame_form, placeholder_text="Precio en $ (Ej: 1.50)", width=130
        )
        self.entry_precio_prod.grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkButton(
            frame_form, text="💾 Guardar Producto", fg_color="green",
            command=self.guardar_producto_db
        ).grid(row=0, column=3, padx=10, pady=10)

        # Tabla productos
        self.tabla_productos = ttk.Treeview(
            self.home_frame,
            columns=("ID", "Nombre", "Categoría", "Precio $", "Precio Bs.", "Estado"),
            show="headings"
        )
        for col in ("ID", "Nombre", "Categoría", "Precio $", "Precio Bs.", "Estado"):
            self.tabla_productos.heading(col, text=col)
        self.tabla_productos.column("ID",         width=40,  anchor="center")
        self.tabla_productos.column("Nombre",     width=200)
        self.tabla_productos.column("Categoría",  width=110, anchor="center")
        self.tabla_productos.column("Precio $",   width=80,  anchor="center")
        self.tabla_productos.column("Precio Bs.", width=110, anchor="center")
        self.tabla_productos.column("Estado",     width=90,  anchor="center")
        self.tabla_productos.pack(pady=10, padx=20, fill="both", expand=True)

        self.cargar_productos()

    def guardar_producto_db(self):
        nombre = self.entry_nombre_prod.get().strip()
        cat    = self.menu_categoria.get()
        precio = self.entry_precio_prod.get().strip()

        if not nombre or not precio:
            messagebox.showwarning("Atención", "Nombre y precio son obligatorios.")
            return
        try:
            precio_val = float(precio)
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número (Ej: 1.50)")
            return

        con = conectar()
        if con:
            try:
                cursor = con.cursor()
                cursor.execute(
                    "INSERT INTO productos (nombre, categoria, precio_usd) VALUES (%s, %s, %s)",
                    (nombre, cat, precio_val)
                )
                con.commit()
                con.close()
                messagebox.showinfo("Éxito", f"Producto '{nombre}' guardado.")
                self.entry_nombre_prod.delete(0, "end")
                self.entry_precio_prod.delete(0, "end")
                self.cargar_productos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def cargar_productos(self):
        for item in self.tabla_productos.get_children():
            self.tabla_productos.delete(item)
        con = conectar()
        if con:
            cursor = con.cursor()
            cursor.execute(
                "SELECT id_producto, nombre, categoria, precio_usd, estado "
                "FROM productos ORDER BY categoria, nombre"
            )
            for fila in cursor.fetchall():
                precio_usd = float(fila[3])
                precio_bs  = precio_usd * self.tasa_bcv
                self.tabla_productos.insert("", "end", values=(
                    fila[0], fila[1], fila[2],
                    f"${precio_usd:.2f}",
                    f"Bs. {precio_bs:,.2f}",
                    fila[4]
                ))
            con.close()

# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()