import customtkinter as ctk
from tkinter import ttk, messagebox
from conexion import conectar

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión - Cantina R.R.")
        self.geometry("1100x680")

        self.tasa_bcv   = self.obtener_tasa_bcv()
        self.carrito    = []
        self.persona_seleccionada = None  # {"id_persona", "nombre", "id_cuenta", "cuenta"}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── BARRA LATERAL ────────────────────────────────────
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            self.navigation_frame, text="  CANTINA R.R.",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=20)

        self.label_tasa_nav = ctk.CTkLabel(
            self.navigation_frame,
            text=f"Tasa BCV:\nBs. {self.tasa_bcv:,.2f}",
            font=ctk.CTkFont(size=12), text_color="lightgreen"
        )
        self.label_tasa_nav.grid(row=1, column=0, padx=20, pady=(0, 10))

        for texto, cmd, fila in [
            ("🛒  Punto de Venta",     self.pos_button_event,       2),
            ("👥  Gestión de Cuentas", self.cuentas_button_event,   3),
            ("🍔  Menú / Productos",   self.productos_button_event, 4),
        ]:
            ctk.CTkButton(
                self.navigation_frame, corner_radius=0, height=40,
                border_spacing=10, text=texto, fg_color="transparent",
                text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                anchor="w", command=cmd
            ).grid(row=fila, column=0, sticky="ew")

        ctk.CTkOptionMenu(
            self.navigation_frame, values=["Dark", "Light", "System"],
            command=lambda m: ctk.set_appearance_mode(m)
        ).grid(row=7, column=0, padx=20, pady=20, sticky="s")

        # ── PANEL PRINCIPAL ──────────────────────────────────
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            self.home_frame,
            text="Bienvenido al Sistema de Gestión\nCantina Escolar R.R.",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=80)
        ctk.CTkLabel(
            self.home_frame, text=f"Tasa BCV activa: Bs. {self.tasa_bcv:,.2f}",
            font=ctk.CTkFont(size=14), text_color="lightgreen"
        ).pack()

    # ============================================================
    # UTILIDADES
    # ============================================================
    def limpiar_panel_derecho(self):
        for w in self.home_frame.winfo_children():
            w.destroy()
        for c in range(3):
            self.home_frame.grid_columnconfigure(c, weight=0)

    def obtener_tasa_bcv(self):
        con = conectar()
        if con:
            try:
                cur = con.cursor()
                cur.execute("SELECT tasa FROM tasa_bcv ORDER BY fecha DESC LIMIT 1")
                r = cur.fetchone()
                con.close()
                if r:
                    return float(r[0])
            except Exception:
                pass
        return 1.0

    # ============================================================
    # MÓDULO: PUNTO DE VENTA
    # ============================================================
    def pos_button_event(self):
        self.limpiar_panel_derecho()
        self.carrito = []
        self.persona_seleccionada = None

        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_columnconfigure(1, weight=0)
        self.home_frame.grid_rowconfigure(0, weight=1)

        # ── COLUMNA IZQUIERDA: PRODUCTOS ─────────────────────
        frame_prod = ctk.CTkFrame(self.home_frame)
        frame_prod.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        frame_prod.grid_rowconfigure(2, weight=1)
        frame_prod.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame_prod, text="Productos Disponibles",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=10)

        self.entry_buscar_pos = ctk.CTkEntry(
            frame_prod, placeholder_text="🔍 Buscar producto...", width=320
        )
        self.entry_buscar_pos.grid(row=1, column=0, pady=5, padx=10)
        self.entry_buscar_pos.bind("<KeyRelease>", self.filtrar_productos_pos)

        cols_p = ("ID", "Producto", "Precio $", "Precio Bs.")
        self.tabla_pos_prod = ttk.Treeview(frame_prod, columns=cols_p, show="headings", height=16)
        for col in cols_p:
            self.tabla_pos_prod.heading(col, text=col)
        self.tabla_pos_prod.column("ID",         width=40,  anchor="center")
        self.tabla_pos_prod.column("Producto",   width=200)
        self.tabla_pos_prod.column("Precio $",   width=80,  anchor="center")
        self.tabla_pos_prod.column("Precio Bs.", width=110, anchor="center")
        self.tabla_pos_prod.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.tabla_pos_prod.bind("<Double-1>", self.añadir_al_carrito)

        ctk.CTkButton(
            frame_prod, text="🛒  Añadir al Carrito  (o doble clic)",
            fg_color="#1f538d", command=self.añadir_al_carrito
        ).grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        # ── COLUMNA DERECHA: CLIENTE + CARRITO ───────────────
        frame_carrito = ctk.CTkFrame(self.home_frame, width=380, fg_color=("#dbdbdb", "#2b2b2b"))
        frame_carrito.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        frame_carrito.grid_columnconfigure(0, weight=1)
        frame_carrito.grid_columnconfigure(1, weight=1)

        # ── SECCIÓN: BUSCADOR DE PERSONA ─────────────────────
        ctk.CTkLabel(
            frame_carrito, text="¿Quién está comprando?",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(12, 4))

        self.entry_buscar_persona = ctk.CTkEntry(
            frame_carrito, placeholder_text="🔍 Buscar por nombre...", width=340
        )
        self.entry_buscar_persona.grid(row=1, column=0, columnspan=2, padx=10, pady=4)
        self.entry_buscar_persona.bind("<KeyRelease>", self.buscar_persona)

        # Lista de resultados de búsqueda
        self.lista_personas = ttk.Treeview(
            frame_carrito,
            columns=("Nombre", "Tipo", "Cuenta"),
            show="headings", height=4
        )
        self.lista_personas.heading("Nombre", text="Nombre")
        self.lista_personas.heading("Tipo",   text="Tipo")
        self.lista_personas.heading("Cuenta", text="Cuenta Familiar")
        self.lista_personas.column("Nombre",  width=140)
        self.lista_personas.column("Tipo",    width=80,  anchor="center")
        self.lista_personas.column("Cuenta",  width=120)
        self.lista_personas.grid(row=2, column=0, columnspan=2, padx=10, pady=4, sticky="ew")
        self.lista_personas.bind("<<TreeviewSelect>>", self.seleccionar_persona)

        # Etiqueta de persona confirmada
        self.label_persona_sel = ctk.CTkLabel(
            frame_carrito, text="⚠️  Sin persona seleccionada",
            font=ctk.CTkFont(size=12), text_color="orange"
        )
        self.label_persona_sel.grid(row=3, column=0, columnspan=2, pady=4)

        ttk.Separator(frame_carrito, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=6
        )

        # ── SECCIÓN: CARRITO ──────────────────────────────────
        ctk.CTkLabel(
            frame_carrito, text="Carrito de Compras",
            font=ctk.CTkFont(size=15, weight="bold")
        ).grid(row=5, column=0, columnspan=2, pady=(4, 4))

        cols_c = ("Producto", "Cant.", "Subtotal $")
        self.tabla_carrito = ttk.Treeview(frame_carrito, columns=cols_c, show="headings", height=8)
        for col in cols_c:
            self.tabla_carrito.heading(col, text=col)
        self.tabla_carrito.column("Producto",   width=160)
        self.tabla_carrito.column("Cant.",      width=50,  anchor="center")
        self.tabla_carrito.column("Subtotal $", width=90,  anchor="center")
        self.tabla_carrito.grid(row=6, column=0, columnspan=2, padx=10, pady=4, sticky="ew")

        ctk.CTkButton(
            frame_carrito, text="🗑️ Quitar",
            fg_color="#7f0000", width=150, command=self.quitar_del_carrito
        ).grid(row=7, column=0, padx=5, pady=5)
        ctk.CTkButton(
            frame_carrito, text="🧹 Vaciar",
            fg_color="#555", width=150, command=self.vaciar_carrito
        ).grid(row=7, column=1, padx=5, pady=5)

        self.label_total_usd = ctk.CTkLabel(
            frame_carrito, text="TOTAL: $0.00",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="lightgreen"
        )
        self.label_total_usd.grid(row=8, column=0, columnspan=2, pady=(12, 2))

        self.label_total_bs = ctk.CTkLabel(
            frame_carrito, text="Bs. 0,00",
            font=ctk.CTkFont(size=13), text_color="lightyellow"
        )
        self.label_total_bs.grid(row=9, column=0, columnspan=2, pady=(0, 8))

        ctk.CTkLabel(frame_carrito, text="Método de pago:").grid(
            row=10, column=0, columnspan=2
        )
        self.combo_metodo_pago = ctk.CTkOptionMenu(
            frame_carrito,
            values=["Efectivo", "Pago Móvil", "Transferencia", "Pendiente"],
            width=320
        )
        self.combo_metodo_pago.grid(row=11, column=0, columnspan=2, pady=6, padx=10)

        ctk.CTkButton(
            frame_carrito, text="✅  FINALIZAR VENTA",
            fg_color="green", height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.finalizar_venta
        ).grid(row=12, column=0, columnspan=2, pady=12, padx=20, sticky="ew")

        self.cargar_productos_pos()

    # ── LÓGICA DEL BUSCADOR DE PERSONAS ──────────────────────
    def buscar_persona(self, event=None):
        texto = self.entry_buscar_persona.get().strip()
        for item in self.lista_personas.get_children():
            self.lista_personas.delete(item)
        if len(texto) < 2:
            return
        con = conectar()
        if con:
            cur = con.cursor()
            cur.execute(
                """SELECT p.id_persona, p.nombre, p.apellido, p.tipo,
                          c.id_cuenta, c.nombre_referencia
                   FROM personas p
                   JOIN cuentas c ON p.id_cuenta = c.id_cuenta
                   WHERE CONCAT(p.nombre, ' ', p.apellido) LIKE %s
                      OR p.nombre LIKE %s OR p.apellido LIKE %s
                   LIMIT 8""",
                (f"%{texto}%", f"%{texto}%", f"%{texto}%")
            )
            for f in cur.fetchall():
                self.lista_personas.insert("", "end", iid=str(f[0]), values=(
                    f"{f[1]} {f[2]}", f[3], f[4]
                ), tags=(str(f[4]), str(f[5])))
            con.close()

    def seleccionar_persona(self, event=None):
        sel = self.lista_personas.selection()
        if not sel:
            return
        id_persona = int(sel[0])
        item       = self.lista_personas.item(sel[0])
        nombre     = item["values"][0]
        tags       = item["tags"]
        id_cuenta  = int(tags[0])
        nom_cuenta = tags[1]

        self.persona_seleccionada = {
            "id_persona": id_persona,
            "nombre":     nombre,
            "id_cuenta":  id_cuenta,
            "cuenta":     nom_cuenta
        }
        self.label_persona_sel.configure(
            text=f"✅  {nombre}  —  Cuenta: {nom_cuenta}",
            text_color="lightgreen"
        )

    # ── LÓGICA DEL CARRITO ────────────────────────────────────
    def cargar_productos_pos(self, filtro=""):
        for item in self.tabla_pos_prod.get_children():
            self.tabla_pos_prod.delete(item)
        con = conectar()
        if con:
            cur = con.cursor()
            sql = ("SELECT id_producto, nombre, precio_usd FROM productos "
                   "WHERE estado='Disponible'" +
                   (" AND nombre LIKE %s" if filtro else "") +
                   " ORDER BY categoria, nombre")
            cur.execute(sql, (f"%{filtro}%",) if filtro else ())
            for f in cur.fetchall():
                p = float(f[2])
                self.tabla_pos_prod.insert("", "end", values=(
                    f[0], f[1], f"${p:.2f}", f"Bs. {p*self.tasa_bcv:,.2f}"
                ))
            con.close()

    def filtrar_productos_pos(self, event=None):
        self.cargar_productos_pos(filtro=self.entry_buscar_pos.get())

    def añadir_al_carrito(self, event=None):
        sel = self.tabla_pos_prod.selection()
        if not sel:
            return
        vals = self.tabla_pos_prod.item(sel[0])["values"]
        id_prod, nombre = vals[0], vals[1]
        precio_usd = float(str(vals[2]).replace("$", ""))

        for prod in self.carrito:
            if prod["id"] == id_prod:
                prod["cantidad"] += 1
                prod["subtotal"] = round(prod["cantidad"] * prod["precio"], 2)
                self.actualizar_tabla_carrito()
                return

        self.carrito.append({
            "id": id_prod, "nombre": nombre,
            "precio": precio_usd, "cantidad": 1, "subtotal": precio_usd
        })
        self.actualizar_tabla_carrito()

    def quitar_del_carrito(self):
        sel = self.tabla_carrito.selection()
        if not sel:
            return
        del self.carrito[self.tabla_carrito.index(sel[0])]
        self.actualizar_tabla_carrito()

    def vaciar_carrito(self):
        self.carrito = []
        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
        total = 0.0
        for p in self.carrito:
            self.tabla_carrito.insert("", "end", values=(
                p["nombre"], p["cantidad"], f"${p['subtotal']:.2f}"
            ))
            total += p["subtotal"]
        self.label_total_usd.configure(text=f"TOTAL: ${total:.2f}")
        self.label_total_bs.configure(text=f"Bs. {total * self.tasa_bcv:,.2f}")

    def finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito vacío", "Agrega productos antes de finalizar.")
            return
        if not self.persona_seleccionada:
            messagebox.showwarning("Sin persona", "Busca y selecciona quién está comprando.")
            return

        id_persona = self.persona_seleccionada["id_persona"]
        id_cuenta  = self.persona_seleccionada["id_cuenta"]
        nombre     = self.persona_seleccionada["nombre"]
        cuenta     = self.persona_seleccionada["cuenta"]
        metodo     = self.combo_metodo_pago.get()
        total_usd  = round(sum(p["subtotal"] for p in self.carrito), 2)
        total_bs   = round(total_usd * self.tasa_bcv, 2)

        con = conectar()
        if con:
            try:
                cur = con.cursor()

                # 1. Insertar transacción con id_persona
                cur.execute(
                    "INSERT INTO transacciones "
                    "(id_cuenta, id_persona, tipo, monto_total_usd, monto_total_bs, "
                    "tasa_aplicada, metodo_pago) "
                    "VALUES (%s, %s, 'Consumo', %s, %s, %s, %s)",
                    (id_cuenta, id_persona, total_usd, total_bs, self.tasa_bcv, metodo)
                )
                id_trans = cur.lastrowid

                # 2. Insertar detalles
                for p in self.carrito:
                    cur.execute(
                        "INSERT INTO detalles_transaccion "
                        "(id_transaccion, id_producto, cantidad, precio_unitario_usd, subtotal_usd) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (id_trans, p["id"], p["cantidad"], p["precio"], p["subtotal"])
                    )

                # 3. Actualizar saldo cuenta
                if metodo == "Pendiente":
                    cur.execute(
                        "UPDATE cuentas SET saldo_deuda = saldo_deuda + %s WHERE id_cuenta = %s",
                        (total_usd, id_cuenta)
                    )
                else:
                    cur.execute(
                        "UPDATE cuentas SET saldo_favor = saldo_favor + %s WHERE id_cuenta = %s",
                        (total_usd, id_cuenta)
                    )

                con.commit()
                con.close()

                messagebox.showinfo(
                    "✅ Venta Registrada",
                    f"Comprador: {nombre}\n"
                    f"Cuenta: {cuenta}\n\n"
                    f"Total: ${total_usd:.2f}  /  Bs. {total_bs:,.2f}\n"
                    f"Método: {metodo}"
                )
                self.vaciar_carrito()
                self.persona_seleccionada = None
                self.label_persona_sel.configure(
                    text="⚠️  Sin persona seleccionada", text_color="orange"
                )
                self.entry_buscar_persona.delete(0, "end")
                for item in self.lista_personas.get_children():
                    self.lista_personas.delete(item)

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
        ).pack(pady=15)

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

        # Tabla cuentas
        self.tabla_cuentas = ttk.Treeview(
            self.home_frame,
            columns=("ID", "Referencia", "Teléfono", "Tipo", "Deuda $", "A Favor $"),
            show="headings", height=6
        )
        for col, w in [("ID",40),("Referencia",200),("Teléfono",130),
                       ("Tipo",110),("Deuda $",90),("A Favor $",90)]:
            self.tabla_cuentas.heading(col, text=col)
            self.tabla_cuentas.column(col, width=w, anchor="center" if col not in ("Referencia","Teléfono") else "w")
        self.tabla_cuentas.pack(pady=5, padx=20, fill="x")
        self.tabla_cuentas.bind("<<TreeviewSelect>>", self.on_cuenta_select)
        self.cargar_cuentas()

        # Personas vinculadas
        ctk.CTkLabel(
            self.home_frame, text="Personas vinculadas:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(8, 0))

        self.tabla_personas_asociadas = ttk.Treeview(
            self.home_frame,
            columns=("Nombre", "Apellido", "Tipo", "Grado/Sección"),
            show="headings", height=3
        )
        for col in ("Nombre", "Apellido", "Tipo", "Grado/Sección"):
            self.tabla_personas_asociadas.heading(col, text=col)
        self.tabla_personas_asociadas.pack(pady=2, padx=20, fill="x")

        ctk.CTkButton(
            self.home_frame, text="➕ Vincular Persona",
            fg_color="#1f538d", command=self.abrir_ventana_persona
        ).pack(pady=4)

        # Historial de pedidos de la cuenta
        ctk.CTkLabel(
            self.home_frame, text="Historial de pedidos:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(8, 0))

        self.tabla_historial = ttk.Treeview(
            self.home_frame,
            columns=("ID", "Persona", "Fecha", "Total $", "Total Bs.", "Método", "Tipo"),
            show="headings", height=5
        )
        for col, w in [("ID",40),("Persona",160),("Fecha",130),
                       ("Total $",80),("Total Bs.",110),("Método",110),("Tipo",80)]:
            self.tabla_historial.heading(col, text=col)
            self.tabla_historial.column(col, width=w, anchor="center")
        self.tabla_historial.pack(pady=2, padx=20, fill="x")
        self.tabla_historial.bind("<<TreeviewSelect>>", self.ver_detalle_pedido)

        ctk.CTkLabel(
            self.home_frame, text="Detalle del pedido seleccionado:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(pady=(8, 0))

        self.tabla_detalle_pedido = ttk.Treeview(
            self.home_frame,
            columns=("Producto", "Cantidad", "Precio Unit. $", "Subtotal $"),
            show="headings", height=4
        )
        for col in ("Producto", "Cantidad", "Precio Unit. $", "Subtotal $"):
            self.tabla_detalle_pedido.heading(col, text=col)
        self.tabla_detalle_pedido.pack(pady=2, padx=20, fill="x")

    def guardar_cuenta_db(self):
        ref  = self.entry_ref_cuenta.get().strip()
        tel  = self.entry_tel_cuenta.get().strip()
        tipo = self.menu_tipo_usuario.get()
        if not ref or not tel:
            messagebox.showwarning("Atención", "Nombre y teléfono son obligatorios.")
            return
        con = conectar()
        if con:
            try:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO cuentas (nombre_referencia, telefono, tipo_usuario) VALUES (%s,%s,%s)",
                    (ref, tel, tipo)
                )
                con.commit(); con.close()
                messagebox.showinfo("Éxito", f"Cuenta '{ref}' creada.")
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
            cur = con.cursor()
            cur.execute(
                "SELECT id_cuenta, nombre_referencia, telefono, tipo_usuario, "
                "saldo_deuda, saldo_favor FROM cuentas ORDER BY nombre_referencia"
            )
            for f in cur.fetchall():
                self.tabla_cuentas.insert("", "end", values=f)
            con.close()

    def on_cuenta_select(self, event=None):
        sel = self.tabla_cuentas.selection()
        if sel:
            id_cuenta = self.tabla_cuentas.item(sel[0])["values"][0]
            self.cargar_personas_asociadas(id_cuenta)
            self.cargar_historial(id_cuenta)

    def cargar_personas_asociadas(self, id_cuenta):
        for item in self.tabla_personas_asociadas.get_children():
            self.tabla_personas_asociadas.delete(item)
        con = conectar()
        if con:
            cur = con.cursor()
            cur.execute(
                "SELECT nombre, apellido, tipo, grado_seccion FROM personas WHERE id_cuenta=%s",
                (id_cuenta,)
            )
            for f in cur.fetchall():
                self.tabla_personas_asociadas.insert("", "end", values=f)
            con.close()

    def cargar_historial(self, id_cuenta):
        for item in self.tabla_historial.get_children():
            self.tabla_historial.delete(item)
        for item in self.tabla_detalle_pedido.get_children():
            self.tabla_detalle_pedido.delete(item)
        con = conectar()
        if con:
            cur = con.cursor()
            cur.execute(
                """SELECT t.id_transaccion,
                          CONCAT(p.nombre, ' ', p.apellido) AS persona,
                          DATE_FORMAT(t.fecha, '%%d/%%m/%%Y %%H:%%i'),
                          t.monto_total_usd, t.monto_total_bs,
                          t.metodo_pago, t.tipo
                   FROM transacciones t
                   LEFT JOIN personas p ON t.id_persona = p.id_persona
                   WHERE t.id_cuenta = %s
                   ORDER BY t.fecha DESC""",
                (id_cuenta,)
            )
            for f in cur.fetchall():
                self.tabla_historial.insert("", "end", iid=str(f[0]), values=(
                    f[0], f[1] or "—", f[2],
                    f"${float(f[3]):.2f}",
                    f"Bs. {float(f[4]):,.2f}",
                    f[5], f[6]
                ))
            con.close()

    def ver_detalle_pedido(self, event=None):
        sel = self.tabla_historial.selection()
        if not sel:
            return
        id_trans = int(sel[0])
        for item in self.tabla_detalle_pedido.get_children():
            self.tabla_detalle_pedido.delete(item)
        con = conectar()
        if con:
            cur = con.cursor()
            cur.execute(
                """SELECT pr.nombre, d.cantidad,
                          d.precio_unitario_usd, d.subtotal_usd
                   FROM detalles_transaccion d
                   JOIN productos pr ON d.id_producto = pr.id_producto
                   WHERE d.id_transaccion = %s""",
                (id_trans,)
            )
            for f in cur.fetchall():
                self.tabla_detalle_pedido.insert("", "end", values=(
                    f[0], f[1],
                    f"${float(f[2]):.2f}",
                    f"${float(f[3]):.2f}"
                ))
            con.close()

    def abrir_ventana_persona(self):
        sel = self.tabla_cuentas.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona primero una cuenta.")
            return
        item      = self.tabla_cuentas.item(sel[0])
        id_cuenta = item["values"][0]
        nom_cta   = item["values"][1]

        v = ctk.CTkToplevel(self)
        v.title(f"Vincular persona a: {nom_cta}")
        v.geometry("420x400")
        v.grab_set()

        entries = {}
        for label, key, ph in [
            ("Nombre:",        "nom",   ""),
            ("Apellido:",      "ape",   ""),
            ("Grado/Sección:", "grado", "Ej: 5to A  (dejar vacío si no aplica)"),
        ]:
            ctk.CTkLabel(v, text=label, font=("Arial", 13)).pack(pady=(10, 2))
            e = ctk.CTkEntry(v, width=280, placeholder_text=ph)
            e.pack()
            entries[key] = e

        ctk.CTkLabel(v, text="Tipo:", font=("Arial", 13)).pack(pady=(10, 2))
        menu_tipo = ctk.CTkOptionMenu(
            v, values=["Estudiante", "Docente", "Obrero", "Administrativo"], width=280
        )
        menu_tipo.pack()

        ctk.CTkButton(
            v, text="💾 Guardar", fg_color="green", width=200,
            command=lambda: self.guardar_persona_db(
                id_cuenta,
                entries["nom"].get(), entries["ape"].get(),
                entries["grado"].get(), menu_tipo.get(), v
            )
        ).pack(pady=20)

    def guardar_persona_db(self, id_cuenta, nombre, apellido, grado, tipo, ventana):
        if not nombre.strip() or not apellido.strip():
            messagebox.showwarning("Atención", "Nombre y apellido son obligatorios.")
            return
        con = conectar()
        if con:
            try:
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO personas (nombre, apellido, tipo, grado_seccion, id_cuenta) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (nombre.strip(), apellido.strip(), tipo, grado.strip() or None, id_cuenta)
                )
                con.commit(); con.close()
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
            frame_form, text="💾 Guardar", fg_color="green",
            command=self.guardar_producto_db
        ).grid(row=0, column=3, padx=10, pady=10)

        self.tabla_productos = ttk.Treeview(
            self.home_frame,
            columns=("ID", "Nombre", "Categoría", "Precio $", "Precio Bs.", "Estado"),
            show="headings"
        )
        for col, w in [("ID",40),("Nombre",200),("Categoría",110),
                       ("Precio $",80),("Precio Bs.",110),("Estado",90)]:
            self.tabla_productos.heading(col, text=col)
            self.tabla_productos.column(col, width=w, anchor="center" if col != "Nombre" else "w")
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
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO productos (nombre, categoria, precio_usd) VALUES (%s,%s,%s)",
                    (nombre, cat, precio_val)
                )
                con.commit(); con.close()
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
            cur = con.cursor()
            cur.execute(
                "SELECT id_producto, nombre, categoria, precio_usd, estado "
                "FROM productos ORDER BY categoria, nombre"
            )
            for f in cur.fetchall():
                p = float(f[3])
                self.tabla_productos.insert("", "end", values=(
                    f[0], f[1], f[2],
                    f"${p:.2f}", f"Bs. {p*self.tasa_bcv:,.2f}", f[4]
                ))
            con.close()

if __name__ == "__main__":
    app = App()
    app.mainloop()