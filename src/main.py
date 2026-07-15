"""
main.py
=======
Sistema de Gestión — Cantina Escolar R.R.
Interfaz gráfica. Esquema v3: pedidos + detalle_pedido + pagos.

Módulos:
  - Dashboard          (métricas del día)
  - Clientes           (alta de cuentas + personas)
  - Registrar Pedido   (el corazón del sistema — botones grandes)
  - Cuentas por Cobrar  (semáforo de deuda + WhatsApp)
  - Productos          (catálogo)
"""

import os
import webbrowser
import urllib.parse
from datetime import date, datetime
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox
import database as db
import styles as s

s.aplicar_tema()

METODOS_PAGO_PEDIDO = [
    "Crédito",
    "Efectivo Bs",
    "Pago Móvil",
    "Transferencia",
    "Efectivo $",
]

GRUPOS_GRADO = {
    "Preescolar/1ro-3ro (7:30)": ["preescolar", "1er", "2do", "3er"],
    "4to-6to (8:30)": ["4to", "5to", "6to"],
    "Bachillerato 1-2 (9:30)": ["1er año", "2do año"],
    "Bachillerato 3-5 (10:10)": ["3er año", "4to año", "5to año"],
}


# ============================================================
# UTILIDADES
# ============================================================


def hoy_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def fmt_fecha(valor) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    return str(valor) if valor else "—"


def fmt_fecha_corta(valor) -> str:
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m")
    return str(valor) if valor else "—"


def wa_limpiar_telefono(telefono: str) -> str:
    solo_numeros = "".join(c for c in telefono if c.isdigit())
    if solo_numeros.startswith("0"):
        solo_numeros = "58" + solo_numeros[1:]
    elif not solo_numeros.startswith("58"):
        solo_numeros = "58" + solo_numeros
    return solo_numeros


def wa_abrir_link(telefono: str, mensaje: str):
    numero = wa_limpiar_telefono(telefono)
    texto = urllib.parse.quote(mensaje)
    url = f"https://wa.me/{numero}?text={texto}"
    try:
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir WhatsApp:\n{e}")


# ============================================================
# COMPONENTES REUTILIZABLES
# ============================================================


class ProductoGrid(ctk.CTkScrollableFrame):
    """Grid de botones de productos. Al tocar llama on_click(id, nombre, precio)."""

    def __init__(self, master, on_click, **kwargs):
        super().__init__(master, **kwargs)
        self._on_click = on_click
        self._btns = []
        self._cols = 3

    def cargar(self, productos: list, color: str):
        for b in self._btns:
            b.destroy()
        self._btns = []
        for i, (id_p, nombre, precio_usd) in enumerate(productos):
            precio = float(precio_usd)
            b = ctk.CTkButton(
                self,
                text=f"{nombre}\n${precio:.2f}",
                width=140,
                height=68,
                font=s.f_bold(),
                fg_color=color,
                hover_color=s.hover(color),
                corner_radius=12,
                command=lambda p=(id_p, nombre, precio): self._on_click(p),
            )
            b.grid(
                row=i // self._cols, column=i % self._cols, padx=5, pady=5, sticky="ew"
            )
            self._btns.append(b)
        for c in range(self._cols):
            self.grid_columnconfigure(c, weight=1)


class CarritoItem(ctk.CTkFrame):
    """Fila del carrito con controles + / - / eliminar."""

    def __init__(
        self, master, producto: dict, tasa: float, on_change, on_delete, **kwargs
    ):
        super().__init__(master, corner_radius=10, fg_color=s.C_CARD, **kwargs)
        self._p, self._tasa = producto, tasa
        self._on_change, self._on_delete = on_change, on_delete
        self._render()

    def _render(self):
        for w in self.winfo_children():
            w.destroy()
        self.grid_columnconfigure(0, weight=1)
        p = self._p
        ctk.CTkLabel(
            self, text=p["nombre"], font=s.f_bold(), text_color=s.C_TEXT, anchor="w"
        ).grid(row=0, column=0, padx=10, pady=(8, 1), sticky="w")
        ctk.CTkLabel(
            self,
            text=f"${p['subtotal']:.2f}  ·  Bs.{p['subtotal']*self._tasa:,.0f}",
            font=s.f_small(),
            text_color=s.C_GREEN,
        ).grid(row=1, column=0, padx=10, pady=(0, 6), sticky="w")

        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=0, column=1, rowspan=2, padx=8, pady=4, sticky="e")
        for txt, color, delta in [("−", s.C_ORANGE, -1), ("+", s.C_GREEN, +1)]:
            ctk.CTkButton(
                ctrl,
                text=txt,
                width=30,
                height=30,
                font=ctk.CTkFont(family=s.FONT, size=16, weight="bold"),
                fg_color=color,
                hover_color=s.hover(color),
                corner_radius=8,
                command=lambda d=delta: self._on_change(self._p, d),
            ).pack(side="left", padx=2)
        ctk.CTkLabel(
            ctrl,
            text=str(p["cantidad"]),
            font=ctk.CTkFont(family=s.FONT, size=15, weight="bold"),
            width=28,
            text_color=s.C_TEXT,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            ctrl,
            text="🗑",
            width=30,
            height=30,
            font=s.f_input(),
            fg_color=s.C_ACCENT,
            hover_color=s.hover(s.C_ACCENT),
            corner_radius=8,
            command=lambda: self._on_delete(self._p),
        ).pack(side="left", padx=(6, 2))


# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión — Cantina R.R.")
        self.geometry("1220x740")
        self.configure(fg_color=s.C_BG)

        self.tasa_bcv: float = 1.0
        self.tasa_fecha: str = "—"
        self.carrito: list = []
        self.persona_sel: dict = None
        self.tab_activa: str = "Por Unidad"
        self.views = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.home = ctk.CTkFrame(self, corner_radius=0, fg_color=s.C_BG)
        self.home.grid(row=0, column=1, sticky="nsew")
        self.home.grid_columnconfigure(0, weight=1)
        self.home.grid_rowconfigure(0, weight=1)

        self._build_nav()
        self._inicializar_tasa()
        self.abrir_dashboard()

    # ── HELPERS DE WIDGETS ───────────────────────────────────
    def _card(self, parent, **kw):
        kw.setdefault("border_width", 2)
        kw.setdefault("border_color", s.C_BORDER)
        return ctk.CTkFrame(
            parent, corner_radius=s.CORNER_CARD, fg_color=s.C_CARD, **kw
        )

    def _btn(self, parent, texto, cmd, color=None, height=None, **kw):
        color = color or s.C_BLUE
        height = height or s.BTN_HEIGHT
        return ctk.CTkButton(
            parent,
            text=texto,
            fg_color=color,
            hover_color=s.hover(color),
            font=s.f_bold(),
            height=height,
            corner_radius=s.CORNER,
            command=cmd,
            **kw,
        )

    def _entry(self, parent, ph="", **kw):
        return ctk.CTkEntry(
            parent,
            placeholder_text=ph,
            font=s.f_normal(),
            height=s.BTN_HEIGHT,
            corner_radius=s.CORNER,
            **kw,
        )

    def _opt(self, parent, values, **kw):
        return ctk.CTkOptionMenu(
            parent,
            values=values,
            font=s.f_normal(),
            height=s.BTN_HEIGHT,
            corner_radius=s.CORNER,
            **kw,
        )

    def _mostrar_vista(self, nombre: str):
        """Sistema de vistas en caché — evita reconstruir todo cada vez."""
        for v in self.views.values():
            v.grid_remove()
        if nombre not in self.views:
            frame = ctk.CTkFrame(self.home, corner_radius=0, fg_color=s.C_BG)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            self.views[nombre] = frame
        self.views[nombre].grid()
        return self.views[nombre]

    # ── TASA BCV ─────────────────────────────────────────────
    def _inicializar_tasa(self):
        try:
            r = db.obtener_tasa_bcv_online()
            db.guardar_tasa_bcv(r["tasa"], hoy_str())
            self.tasa_bcv, self.tasa_fecha = r["tasa"], r["fecha"]
        except Exception:
            try:
                r = db.obtener_tasa_bcv()
                self.tasa_bcv, self.tasa_fecha = r["tasa"], r["fecha"]
            except Exception as e:
                messagebox.showwarning(
                    "Sin tasa BCV", f"No se pudo cargar la tasa.\n\n{e}"
                )
        self._actualizar_label_tasa()

    def _actualizar_label_tasa(self):
        if hasattr(self, "_lbl_tasa"):
            self._lbl_tasa.configure(text=f"Bs {self.tasa_bcv:,.2f}")
        if hasattr(self, "_lbl_tasa_fecha"):
            self._lbl_tasa_fecha.configure(text=self.tasa_fecha)

    def _tasa_actualizar_online(self):
        try:
            r = db.obtener_tasa_bcv_online()
            db.guardar_tasa_bcv(r["tasa"], hoy_str())
            self.tasa_bcv, self.tasa_fecha = r["tasa"], r["fecha"]
            self._actualizar_label_tasa()
            messagebox.showinfo("✅", f"Tasa actualizada: Bs. {self.tasa_bcv:,.2f}")
        except Exception as e:
            messagebox.showwarning("Sin conexión", str(e))

    def _tasa_manual(self):
        v = ctk.CTkToplevel(self)
        v.title("Tasa Manual")
        v.geometry("360x220")
        v.grab_set()
        ctk.CTkLabel(v, text="Ingresar Tasa BCV Manual", font=s.f_subtitulo()).pack(
            pady=(20, 10)
        )
        e = self._entry(v, ph="Ej: 517.96")
        e.pack(pady=6, padx=24, fill="x")

        def guardar():
            try:
                tasa = float(e.get().strip().replace(",", "."))
                if tasa <= 0:
                    raise ValueError
                db.guardar_tasa_bcv(tasa, hoy_str())
                self.tasa_bcv = tasa
                self.tasa_fecha = date.today().strftime("%d/%m/%Y")
                self._actualizar_label_tasa()
                messagebox.showinfo("✅", f"Tasa: Bs. {tasa:,.2f}")
                v.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingresa un número válido.", parent=v)

        self._btn(v, "💾  Guardar", guardar, color=s.C_GREEN).pack(
            pady=16, padx=24, fill="x"
        )

    # ── NAVEGACIÓN ───────────────────────────────────────────
    def _build_nav(self):
        nav = ctk.CTkFrame(self, corner_radius=0, fg_color=s.C_NAV, width=210)
        nav.grid(row=0, column=0, sticky="nsew")
        nav.grid_propagate(False)
        nav.grid_rowconfigure(9, weight=1)

        # --- NUEVO: Carga de logo con ruta segura ---
        ruta_logo = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

        # Puedes ajustar el valor (80, 80) si necesitas el logo más grande o pequeño
        img_logo = ctk.CTkImage(
            light_image=Image.open(ruta_logo),
            dark_image=Image.open(ruta_logo),
            size=(80, 80),
        )

        ctk.CTkLabel(nav, image=img_logo, text="").grid(row=0, column=0, pady=(22, 2))
        # ---------------------------------------------

        ctk.CTkLabel(
            nav,
            text="CANTINA R.R.",
            font=s.f_nav(),
            text_color="white",
        ).grid(row=1, column=0, pady=(0, 8))

        # ── Panel BCV: panel claro sobre fondo oscuro del nav ──
        bcv_panel = ctk.CTkFrame(
            nav,
            corner_radius=s.CORNER,
            fg_color=("#1a5c3e", "#0e2d1e"),
            border_width=1,
            border_color=("#2e8b5a", "#1a4530"),
        )
        bcv_panel.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            bcv_panel,
            text="TASA BCV",
            font=s.f_badge(),
            text_color=("#6dbf8a", "#6dbf8a"),
        ).pack(pady=(8, 0))

        # Valor de la tasa — grande y legible
        self._lbl_tasa = ctk.CTkLabel(
            bcv_panel,
            text="—",
            font=s.f_seccion(),  # 17px bold — visible desde lejos
            text_color="#ffffff",
        )
        self._lbl_tasa.pack(pady=(2, 0))

        # Fecha — subtítulo pequeño
        self._lbl_tasa_fecha = ctk.CTkLabel(
            bcv_panel,
            text="Cargando...",
            font=s.f_small(),
            text_color=("#8ab8a0", "#6a9a84"),
        )
        self._lbl_tasa_fecha.pack(pady=(1, 4))

        btn_row = ctk.CTkFrame(bcv_panel, fg_color="transparent")
        btn_row.pack(pady=(0, 8))

        img_refresh = self._cargar_icono("recarga.png", size=(14, 14))
        img_edit = self._cargar_icono("lapiz.png", size=(14, 14))

        for icono, cmd, tooltip in [
            (img_refresh, self._tasa_actualizar_online, "↻"),
            (img_edit, self._tasa_manual, "✏"),
        ]:
            ctk.CTkButton(
                btn_row,
                text="",
                image=icono,
                width=38,
                height=30,
                fg_color=("#393B39", "#2d2e2d"),
                hover_color=("#2e8b5a", "#1d5c3f"),
                corner_radius=8,
                command=cmd,
            ).pack(side="left", padx=3)

        items = [
            ("dashboard.png", "Dashboard", self.abrir_dashboard, 3),
            ("apreton.png", "Clientes", self.abrir_clientes, 4),
            ("recipe.png", "Registrar Pedido", self.abrir_pedidos, 5),
            ("tarjeta.png", "Cuentas por Cobrar", self.abrir_cobrar, 6),
            ("hamburguesa.png", "Productos", self.abrir_productos, 7),
        ]
        for archivo_icono, texto, cmd, fila in items:
            f = ctk.CTkFrame(nav, fg_color="transparent", cursor="hand2")
            f.grid(row=fila, column=0, sticky="ew", padx=10, pady=3)
            f.grid_columnconfigure(1, weight=1)

            # Helper para cargar imagen al menu
            icono_img = self._cargar_icono(archivo_icono, size=(22, 22))

            # label para la imagen sin texto
            ctk.CTkLabel(f, text="", image=icono_img, width=32).grid(
                row=0, column=0, padx=(10, 4)
            )

            # label para el texto del menu
            ctk.CTkLabel(
                f, text=texto, font=s.f_nav(), text_color="white", anchor="w"
            ).grid(row=0, column=1, sticky="ew")

            # eventos de hover y click se mantiene igual
            for w in [f] + list(f.winfo_children()):
                w.bind("<Button-1>", lambda e, c=cmd: c())
                w.bind(
                    "<Enter>",
                    lambda e, fr=f: fr.configure(fg_color=s.C_NAV_ITEM),
                )
                w.bind("<Leave>", lambda e, fr=f: fr.configure(fg_color="transparent"))

        self._opt(
            nav,
            ["Dark", "Light", "System"],
            fg_color=("#1f6b4a", "#112e1e"),
            button_color=("#27855c", "#1a4030"),
            command=lambda m: ctk.set_appearance_mode(m),
        ).grid(row=10, column=0, padx=16, pady=16, sticky="ew")

    def _cargar_icono(self, nombre_archivo, size=(20, 20)):
        """Carga una imagen desde la carpeta assets y la convierte en CTkImage"""
        ruta = os.path.join(os.path.dirname(__file__), "assets", nombre_archivo)
        return ctk.CTkImage(
            light_image=Image.open(ruta), dark_image=Image.open(ruta), size=size
        )

    # ============================================================
    # MÓDULO: DASHBOARD
    # ============================================================

    def abrir_dashboard(self):
        container = self._mostrar_vista("dashboard")
        self._dash_refrescar(container)

    def _dash_refrescar(self, container):
        for w in container.winfo_children():
            w.destroy()
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=1)

        try:
            m = db.obtener_metricas_dia(hoy_str())
        except Exception as e:
            messagebox.showerror("Error", str(e))
            m = {
                "total_pedidos": 0,
                "ventas_usd": 0,
                "pedidos_pagados": 0,
                "pedidos_pendientes": 0,
                "cobrado_usd": 0,
                "deuda_total_usd": 0,
            }

        # Cabecera — verde oscuro para contraste visual inmediato
        cab = ctk.CTkFrame(container, corner_radius=s.CORNER_CARD, fg_color=s.C_NAV)
        cab.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 6))

        dia_semana = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        }.get(date.today().strftime("%A"), "")

        # icono de cabecera
        img_dash = self._cargar_icono("dashboard.png", size=(24, 24))

        ctk.CTkLabel(
            cab,
            text=f"  Buenos días — Hoy es {dia_semana}",
            image=img_dash,
            compound="left",
            font=s.f_subtitulo(),
            text_color="#ffffff",
        ).pack(pady=14, padx=16, anchor="w")

        # Grid de métricas
        grid = ctk.CTkScrollableFrame(container, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        for c in range(4):
            grid.grid_columnconfigure(c, weight=1)

    # ── TARJETAS DE MÉTRICAS ───────────────────────────────

        tarjetas = [
            ("recipe.png", "Pedidos hoy", str(m["total_pedidos"]), s.C_BLUE),
            ("check.png", "Pagados", str(m["pedidos_pagados"]), s.C_GREEN),
            ("relojarena.png", "Pendientes", str(m["pedidos_pendientes"]), s.C_ORANGE),
            ("dinero.png", "Ventas del día", f"${m['ventas_usd']:.2f}", s.C_YELLOW),
            ("bolsa_dinero.png", "Cobrado hoy", f"${m['cobrado_usd']:.2f}", s.C_GREEN),
            ("deuda.png", "Deuda acumulada", f"${m['deuda_total_usd']:.2f}", s.C_ACCENT),
        ]

        for i, (archivo_icono, titulo, valor, color) in enumerate(tarjetas):
            card = self._card(grid)
            card.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew")    
            img_tarjeta = self._cargar_icono(archivo_icono, size=(32, 32))
            
            # Renderizado de la tarjeta
            ctk.CTkLabel(card, text="", image=img_tarjeta).pack(pady=(16, 2))
            ctk.CTkLabel(card, text=valor, font=s.f_titulo(), text_color=color).pack()
            ctk.CTkLabel(card, text=titulo, font=s.f_small(), text_color=s.C_SUBTEXT).pack(pady=(2, 16))

        img_trofeo = self._cargar_icono("trofeo.png", size=(20, 20))

        # Productos más vendidos
        ctk.CTkLabel(
            grid,
            text="   Productos más vendidos (histórico)",
            font=s.f_bold(),
            text_color=s.C_TEXT,
            image=img_trofeo,
            compound="left",
        ).grid(row=2, column=0, columnspan=4, pady=(14, 6), sticky="w")
        
        try:
            top = db.obtener_productos_mas_vendidos(5)
        except Exception:
            top = []
            
        if not top:
            ctk.CTkLabel(
                grid,
                text="Aún no hay ventas registradas.",
                font=s.f_normal(),
                text_color=s.C_SUBTEXT,
            ).grid(row=3, column=0, columnspan=4, sticky="w")
        else:
            for i, (nombre, cantidad, ingresos) in enumerate(top):
                fila = self._card(grid)
                fila.grid(row=3 + i, column=0, columnspan=4, sticky="ew", padx=4, pady=3)
                fila.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(
                    fila, text=f"#{i+1}", font=s.f_bold(), text_color=s.C_PURPLE, width=40,
                ).grid(row=0, column=0, padx=(12, 4), pady=10)
                ctk.CTkLabel(
                    fila, text=nombre, font=s.f_bold(), text_color=s.C_TEXT, anchor="w"
                ).grid(row=0, column=1, sticky="w", pady=10)
                ctk.CTkLabel(
                    fila,
                    text=f"{int(cantidad)} vendidos  ·  ${float(ingresos):.2f}",
                    font=s.f_small(),
                    text_color=s.C_GREEN,
                ).grid(row=0, column=2, padx=12, pady=10)

        # =========================================================
        # NUEVO: TERCER SUB-ÍTEM - HISTORIAL DE TRANSACCIONES
        # (Ahora sí, correctamente ubicado al final del grid del Dashboard)
        # =========================================================
        fila_historial = 10
        img_historial = self._cargar_icono("recipe.png", size=(20, 20))

        ctk.CTkLabel(
            grid,
            text="   Historial de Transacciones (Consulta)",
            font=s.f_bold(),
            text_color=s.C_TEXT,
            image=img_historial,
            compound="left",
        ).grid(row=fila_historial, column=0, columnspan=2, pady=(24, 6), sticky="w")

        # Buscador dinámico para las transacciones
        self._e_buscar_transaccion = self._entry(grid, ph="🔍 Buscar por alumno o referencia...")
        self._e_buscar_transaccion.grid(row=fila_historial, column=2, columnspan=2, sticky="ew", padx=4, pady=(24, 6))
        self._e_buscar_transaccion.bind("<KeyRelease>", self._dash_filtrar_transacciones)

        # Contenedor dedicado para la lista
        self._frame_transacciones = ctk.CTkFrame(grid, fg_color="transparent")
        self._frame_transacciones.grid(row=fila_historial + 1, column=0, columnspan=4, sticky="nsew", pady=4)
        self._frame_transacciones.grid_columnconfigure(0, weight=1)

        # Llamada inicial para cargar la lista de transacciones
        self._dash_cargar_transacciones()

    # ------------------------------------------------------------
    # FUNCIONES LÓGICAS PARA LAS TRANSACCIONES (Nivel de clase App)
    # ------------------------------------------------------------

    def _dash_filtrar_transacciones(self, event=None):
        """Captura el texto del buscador y recarga la lista."""
        txt = self._e_buscar_transaccion.get().strip()
        self._dash_cargar_transacciones(txt)

    def _dash_cargar_transacciones(self, filtro: str = ""):
        """Obtiene y dibuja el historial de pedidos desde la BD."""
        for w in self._frame_transacciones.winfo_children():
            w.destroy()

        try:
            pedidos = db.obtener_pedidos(filtro=filtro) 
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        if not pedidos:
            ctk.CTkLabel(
                self._frame_transacciones,
                text="No se encontraron transacciones registradas.",
                font=s.f_normal(),
                text_color=s.C_SUBTEXT,
            ).pack(pady=20)
            return

        for ped in pedidos:
            id_pedido, nombre_persona, grado, nombre_cuenta, fecha, total_usd, estado_pago, pagado_usd = ped

            card = self._card(self._frame_transacciones)
            card.pack(fill="x", padx=4, pady=3)
            card.grid_columnconfigure(1, weight=1) 

            # 1. Fecha
            ctk.CTkLabel(
                card,
                text=fmt_fecha(fecha),
                font=s.f_small(),
                text_color=s.C_SUBTEXT,
                width=130,
                anchor="w"
            ).grid(row=0, column=0, padx=(12, 4), pady=10, sticky="w")

            # 2. Datos del Cliente
            ctk.CTkLabel(
                card,
                text=f"{nombre_persona} ({grado})  ·  Ref: {nombre_cuenta}",
                font=s.f_bold(),
                text_color=s.C_TEXT,
                anchor="w"
            ).grid(row=0, column=1, sticky="w", pady=10)

            # 3. Monto Total
            ctk.CTkLabel(
                card,
                text=f"${float(total_usd):.2f}",
                font=s.f_bold(),
                text_color=s.C_TEXT,
            ).grid(row=0, column=2, padx=12, pady=10)

            # 4. Estado de Pago
            color_est = s.C_GREEN if estado_pago == "Pagado" else (s.C_ORANGE if estado_pago == "Parcial" else s.C_ACCENT)
            
            ctk.CTkLabel(
                card,
                text=estado_pago.upper(),
                font=s.f_small() if not hasattr(s, 'f_badge') else s.f_badge(),
                text_color=color_est,
                width=80
            ).grid(row=0, column=3, padx=(0, 12), pady=10)
            
    # ============================================================
    # MÓDULO: CLIENTES (alta de cuentas y personas)
    # ============================================================

    def abrir_clientes(self):
        container = self._mostrar_vista("clientes")
        # Siempre refrescamos la lista al abrir
        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=1)
            container.grid_columnconfigure(1, weight=1)
            container.grid_rowconfigure(0, weight=1)

            # ── IZQUIERDA: LISTA DE CLIENTES ─────────────────────
            fl = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fl.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
            fl.grid_rowconfigure(1, weight=1)
            fl.grid_columnconfigure(0, weight=1)

            top = self._card(fl)
            top.pack(fill="x", pady=(0, 8))

            img_clientes = self._cargar_icono("clientes.png", size=(18, 18))

            ctk.CTkLabel(
                top,
                text="   Clientes Registrados",
                font=s.f_subtitulo(),
                text_color=s.C_TEXT,
                image=img_clientes,
                compound="left",
            ).pack(pady=(12, 4), padx=14, anchor="w")
            self._e_cli_buscar = self._entry(
                top, ph="🔍  Buscar por nombre o apellido..."
            )
            self._e_cli_buscar.pack(fill="x", padx=14, pady=(0, 12))
            self._e_cli_buscar.bind("<KeyRelease>", self._cli_buscar)

            self._frame_cli_resultados = ctk.CTkScrollableFrame(
                fl, fg_color="transparent", corner_radius=0
            )
            self._frame_cli_resultados.pack(fill="both", expand=True)

            # ── DERECHA: FORMULARIO NUEVO CLIENTE ────────────────
            fr = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fr.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

            form = self._card(fr)
            form.pack(fill="x")
            ctk.CTkLabel(
                form,
                text="➕  Nuevo Cliente",
                font=s.f_subtitulo(),
                text_color=s.C_TEXT,
            ).pack(pady=(14, 8), padx=16, anchor="w")

            fila_tipo = ctk.CTkFrame(form, fg_color="transparent")
            fila_tipo.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(fila_tipo, text="Tipo:", font=s.f_normal()).pack(
                side="left", padx=(0, 8)
            )
            self._m_cli_tipo = self._opt(
                fila_tipo, s.TIPOS_USUARIO, command=self._cli_toggle_campos
            )
            self._m_cli_tipo.pack(side="left", fill="x", expand=True)

            self._e_cli_nombre = self._entry(form, ph="Nombre")
            self._e_cli_nombre.pack(fill="x", padx=16, pady=5)

            self._e_cli_apellido = self._entry(form, ph="Apellido")
            self._e_cli_apellido.pack(fill="x", padx=16, pady=5)

            # Nivel/Cargo — dropdown para estudiantes, texto para otros
            self._frame_nivel_cargo = ctk.CTkFrame(form, fg_color="transparent")
            self._frame_nivel_cargo.pack(fill="x")
            self._m_cli_nivel = self._opt(self._frame_nivel_cargo, s.NIVELES_ESTUDIANTE)
            self._e_cli_cargo = self._entry(
                self._frame_nivel_cargo, ph="Cargo (opcional)"
            )
            # La visibilidad inicial la fija _cli_toggle_campos al final

            ctk.CTkLabel(
                form,
                text="Datos del representante:",
                font=s.f_bold(),
                text_color=s.C_SUBTEXT,
            ).pack(pady=(8, 2), padx=16, anchor="w")

            self._e_cli_referencia = self._entry(
                form, ph="Nombre referencia  (Ej: Hermanos Silva)"
            )
            self._e_cli_referencia.pack(fill="x", padx=16, pady=5)

            # Teléfono con prefijo automático
            fila_tel = ctk.CTkFrame(form, fg_color="transparent")
            fila_tel.pack(fill="x", padx=16, pady=5)
            fila_tel.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                fila_tel,
                text="58",
                font=s.f_bold(),
                fg_color=(s.C_PRIMARY, "#0d2318"),
                corner_radius=8,
                width=38,
                text_color="white",
            ).grid(row=0, column=0, padx=(0, 6), ipady=8)
            self._e_cli_tel = self._entry(fila_tel, ph="4121234567  (sin el 0 inicial)")
            self._e_cli_tel.grid(row=0, column=1, sticky="ew")

            ctk.CTkLabel(
                form,
                text="El prefijo 58 se agrega automáticamente.",
                font=s.f_small(),
                text_color=s.C_SUBTEXT,
            ).pack(padx=16, pady=(0, 4), anchor="w")

            # cargamos el icono de guardar
            img_guardar = self._cargar_icono("guardar.png", size=(18, 18))

            self._btn(
                form,
                "   Guardar Cliente",
                self._cli_guardar,
                color=s.C_GREEN,
                image=img_guardar,
            ).pack(fill="x", padx=16, pady=(8, 16))

            self._cli_toggle_campos(self._m_cli_tipo.get())

        self._cli_cargar_todos()

    def _cli_toggle_campos(self, tipo: str):
        """Alterna entre dropdown de nivel (Estudiante) y campo de cargo (otros)."""
        for w in self._frame_nivel_cargo.winfo_children():
            w.pack_forget()
        if tipo == "Estudiante":
            self._m_cli_nivel.pack(fill="x", padx=16, pady=5)
        else:
            self._e_cli_cargo.pack(fill="x", padx=16, pady=5)

    def _cli_cargar_todos(self):
        """Muestra todos los clientes registrados."""
        for w in self._frame_cli_resultados.winfo_children():
            w.destroy()
        try:
            filas = db.buscar_personas("")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if not filas:
            ctk.CTkLabel(
                self._frame_cli_resultados,
                text="No hay clientes registrados aún.\nCrea el primero →",
                font=s.f_normal(),
                text_color=s.C_SUBTEXT,
            ).pack(pady=30)
            return
        self._cli_renderizar(filas)

    def _cli_buscar(self, event=None):
        txt = self._e_cli_buscar.get().strip()
        if len(txt) < 2:
            self._cli_cargar_todos()
            return
        try:
            filas = db.buscar_personas(txt)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for w in self._frame_cli_resultados.winfo_children():
            w.destroy()
        if not filas:
            ctk.CTkLabel(
                self._frame_cli_resultados,
                text="Sin resultados. Puedes crearlo →",
                font=s.f_normal(),
                text_color=s.C_ORANGE,
            ).pack(pady=20)
            return
        self._cli_renderizar(filas)

    def _cli_renderizar(self, filas: list):
        """Dibuja la lista de clientes con botones de editar y eliminar."""

        # cargar los iconos de editar y eliminar
        img_editar = self._cargar_icono("lapiz.png", size=(16, 16))
        img_eliminar = self._cargar_icono("borrar.png", size=(16, 16))

        for f in filas:
            id_p, nom, ape, tipo, grado, id_c, ref, tel = f
            card = self._card(self._frame_cli_resultados)
            card.pack(fill="x", padx=4, pady=4)
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card,
                text=f"{nom} {ape}",
                font=s.f_bold(),
                text_color=s.C_TEXT,
                anchor="w",
            ).grid(row=0, column=0, padx=12, pady=(8, 1), sticky="w")
            sub = tipo + (f" · {grado}" if grado else "") + f"  ·  {ref}  ·  📞{tel}"
            ctk.CTkLabel(
                card, text=sub, font=s.f_small(), text_color=s.C_SUBTEXT, anchor="w"
            ).grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")

            bf = ctk.CTkFrame(card, fg_color="transparent")
            bf.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
            self._btn(
                bf,
                "   Editar",
                lambda d=(
                    id_p,
                    nom,
                    ape,
                    tipo,
                    grado,
                    id_c,
                    ref,
                    tel,
                ): self._cli_editar(d),
                color="#555",
                height=30,
                image=img_editar,
            ).pack(side="left", padx=4)
            self._btn(
                bf,
                "   Eliminar",
                lambda i=id_p, n=f"{nom} {ape}": self._cli_eliminar(i, n),
                color=s.C_ACCENT,
                height=30,
                image=img_eliminar,
            ).pack(side="left", padx=4)

    def _cli_editar(self, datos: tuple):
        id_p, nom, ape, tipo, grado, id_c, ref, tel = datos
        v = ctk.CTkToplevel(self)
        v.title("Editar Cliente")
        v.geometry("420x560")
        v.grab_set()
        ctk.CTkLabel(v, text="✏️  Editar Cliente", font=s.f_subtitulo()).pack(
            pady=(18, 8)
        )

        m_tipo = self._opt(v, s.TIPOS_USUARIO)
        m_tipo.set(tipo)
        m_tipo.pack(pady=5, padx=24, fill="x")
        e_nom = self._entry(v, ph="Nombre")
        e_nom.insert(0, nom)
        e_nom.pack(pady=5, padx=24, fill="x")
        e_ape = self._entry(v, ph="Apellido")
        e_ape.insert(0, ape)
        e_ape.pack(pady=5, padx=24, fill="x")
        # Nivel/cargo — igual que en el formulario de creación
        frame_nivel_e = ctk.CTkFrame(v, fg_color="transparent")
        frame_nivel_e.pack(fill="x", padx=24, pady=5)
        m_nivel_e = self._opt(frame_nivel_e, s.NIVELES_ESTUDIANTE)
        e_cargo_e = self._entry(frame_nivel_e, ph="Cargo (opcional)")

        def _toggle_nivel_e(t):
            for w in frame_nivel_e.winfo_children():
                w.pack_forget()
            if t == "Estudiante":
                m_nivel_e.pack(fill="x")
                if (grado or "") in s.NIVELES_ESTUDIANTE:
                    m_nivel_e.set(grado)
            else:
                e_cargo_e.pack(fill="x")
                e_cargo_e.delete(0, "end")
                e_cargo_e.insert(0, grado or "")

        m_tipo.configure(command=_toggle_nivel_e)
        _toggle_nivel_e(tipo)  # estado inicial

        ctk.CTkLabel(
            v, text="Representante:", font=s.f_bold(), text_color=s.C_SUBTEXT
        ).pack(pady=(8, 2), padx=24, anchor="w")
        e_ref = self._entry(v, ph="Nombre referencia")
        e_ref.insert(0, ref)
        e_ref.pack(pady=5, padx=24, fill="x")

        # Teléfono — mostrar sin el 58 inicial para edición cómoda
        tel_sin_prefijo = tel[2:] if tel.startswith("58") else tel
        fila_tel = ctk.CTkFrame(v, fg_color="transparent")
        fila_tel.pack(fill="x", padx=24, pady=5)
        fila_tel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            fila_tel,
            text="58",
            font=s.f_bold(),
            fg_color=(s.C_PRIMARY, "#0d2318"),
            corner_radius=8,
            width=38,
            text_color="#ffffff",
        ).grid(row=0, column=0, padx=(0, 6), ipady=8)
        e_tel = self._entry(fila_tel)
        e_tel.insert(0, tel_sin_prefijo)
        e_tel.grid(row=0, column=1, sticky="ew")

        def guardar():
            t = m_tipo.get()
            nuevo_grado = (
                m_nivel_e.get() if t == "Estudiante" else e_cargo_e.get().strip()
            )
            nuevo_tel = "58" + e_tel.get().strip().lstrip("0")
            try:
                db.actualizar_persona(
                    id_p,
                    e_nom.get().strip(),
                    e_ape.get().strip(),
                    m_tipo.get(),
                    nuevo_grado,
                )
                db.actualizar_cuenta(id_c, e_ref.get().strip(), nuevo_tel, m_tipo.get())
                messagebox.showinfo("✅", "Cliente actualizado.", parent=v)
                self._cli_cargar_todos()
                v.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=v)

        self._btn(v, "💾  Guardar", guardar, color=s.C_GREEN).pack(
            pady=14, padx=24, fill="x"
        )

    def _cli_eliminar(self, id_persona: int, nombre: str):
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar a {nombre}?\nSe borrarán también sus pedidos asociados.",
        ):
            return
        try:
            db.eliminar_persona(id_persona)
            messagebox.showinfo("✅", f"{nombre} eliminado.")
            self._cli_cargar_todos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cli_guardar(self):
        tipo = self._m_cli_tipo.get()
        nombre = self._e_cli_nombre.get().strip()
        ape = self._e_cli_apellido.get().strip()
        # Nivel para estudiantes, cargo para el resto
        if tipo == "Estudiante":
            grado = self._m_cli_nivel.get()
        else:
            grado = self._e_cli_cargo.get().strip()
        ref = self._e_cli_referencia.get().strip()
        tel_raw = self._e_cli_tel.get().strip()

        if not nombre or not ape or not ref or not tel_raw:
            messagebox.showwarning(
                "Atención", "Nombre, apellido, referencia y teléfono son obligatorios."
            )
            return
        # Construir teléfono con prefijo 58
        tel = "58" + tel_raw.lstrip("0")
        try:
            id_cuenta = db.crear_cuenta(ref, tel, tipo)
            db.crear_persona(nombre, ape, tipo, grado, id_cuenta)
            messagebox.showinfo(
                "✅ Cliente creado",
                f'{nombre} {ape} registrado bajo la cuenta "{ref}".',
            )
            self._e_cli_nombre.delete(0, "end")
            self._e_cli_apellido.delete(0, "end")
            self._m_cli_nivel.set(s.NIVELES_ESTUDIANTE[0])
            self._e_cli_cargo.delete(0, "end")
            self._e_cli_referencia.delete(0, "end")
            self._e_cli_tel.delete(0, "end")
            self._cli_cargar_todos()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ============================================================
    # MÓDULO: REGISTRAR PEDIDO (el corazón del sistema)
    # ============================================================

    def abrir_pedidos(self):
        container = self._mostrar_vista("pedidos")
        self.carrito = []
        self.persona_sel = None

        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=3)
            container.grid_columnconfigure(1, weight=2)
            container.grid_rowconfigure(0, weight=1)

            # ── IZQUIERDA: CATÁLOGO ──────────────────────────
            fl = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fl.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
            fl.grid_rowconfigure(2, weight=1)
            fl.grid_columnconfigure(0, weight=1)

            self._e_buscar_prod_pedido = self._entry(fl, ph="🔍  Buscar producto...")
            self._e_buscar_prod_pedido.grid(
                row=0, column=0, sticky="ew", padx=4, pady=(4, 8)
            )
            self._e_buscar_prod_pedido.bind("<KeyRelease>", self._ped_filtrar_prod)

            tabs = ctk.CTkFrame(fl, fg_color="transparent")
            tabs.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 6))
            self._tab_btns = {}
            for cat in s.CATEGORIAS:
                b = ctk.CTkButton(
                    tabs,
                    text=cat,
                    height=34,
                    font=s.f_small_bold(),
                    fg_color=s.CAT_COLORS[cat],
                    hover_color=s.hover(s.CAT_COLORS[cat]),
                    corner_radius=18,
                    command=lambda c=cat: self._ped_cambiar_tab(c),
                )
                b.pack(side="left", padx=4)
                self._tab_btns[cat] = b

            self._prod_grid = ProductoGrid(
                fl, on_click=self._ped_agregar, fg_color="transparent", corner_radius=0
            )
            self._prod_grid.grid(row=2, column=0, sticky="nsew", padx=4)

            # ── DERECHA: CLIENTE + CARRITO ────────────────────
            fr = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG2)
            fr.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
            fr.grid_columnconfigure(0, weight=1)
            fr.grid_rowconfigure(0, weight=0)  # panel persona: fijo
            fr.grid_rowconfigure(2, weight=1)  # carrito: se expande

            # ── Panel "¿Quién pide?" — compacto en una sola fila ──
            top_r = self._card(fr)
            top_r.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
            top_r.grid_columnconfigure(0, weight=1)
            top_r.grid_columnconfigure(1, weight=0)

            ctk.CTkLabel(
                top_r, text="¿Quién pide?", font=s.f_bold(), text_color=s.C_TEXT
            ).grid(row=0, column=0, columnspan=2, pady=(8, 4), padx=12, sticky="w")

            self._e_persona = self._entry(top_r, ph="🔍  Nombre del alumno...")
            self._e_persona.grid(row=1, column=0, sticky="ew", padx=(10, 4), pady=4)
            self._e_persona.bind("<KeyRelease>", self._ped_buscar_persona)

            self._lbl_persona = ctk.CTkLabel(
                top_r,
                text="⚠️  Selecciona quién pide",
                font=s.f_badge(),
                text_color=s.C_ORANGE,
            )
            self._lbl_persona.grid(row=2, column=0, columnspan=2, pady=(2, 6), padx=12)

            # Resultados de búsqueda — altura reducida
            self._frame_res_persona = ctk.CTkScrollableFrame(
                top_r, height=65, fg_color="transparent"
            )
            self._frame_res_persona.grid(
                row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8)
            )

            # icono de detalle del pedido
            img_detalle = self._cargar_icono("pagina.png", size=(20, 20))

            # ── Título carrito ────────────────────────────────────
            ctk.CTkLabel(
                fr,
                text="   Detalle del Pedido",
                font=s.f_subtitulo(),
                text_color=s.C_TEXT,
                image=img_detalle,
                compound="left",
            ).grid(row=1, column=0, pady=(4, 2), padx=14, sticky="w")

            # ── Carrito — ocupa todo el espacio disponible ────────
            self._frame_carrito = ctk.CTkScrollableFrame(
                fr, fg_color="transparent", corner_radius=0
            )
            self._frame_carrito.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)
            self._frame_carrito.grid_columnconfigure(0, weight=1)

            # ── Footer con totales y método de pago ───────────────
            footer = self._card(fr)
            footer.grid(row=3, column=0, sticky="ew", padx=10, pady=(4, 6))
            footer.grid_columnconfigure(0, weight=1)
            footer.grid_columnconfigure(1, weight=1)

            self._lbl_total_usd = ctk.CTkLabel(
                footer, text="$0.00", font=s.f_total(), text_color=s.C_GREEN
            )
            self._lbl_total_usd.grid(row=0, column=0, columnspan=2, pady=(8, 1))

            self._lbl_total_bs = ctk.CTkLabel(
                footer, text="Bs. 0", font=s.f_normal(), text_color=s.C_YELLOW
            )
            self._lbl_total_bs.grid(row=1, column=0, columnspan=2, pady=(0, 4))

            self._combo_metodo = self._opt(
                footer,
                METODOS_PAGO_PEDIDO,
                fg_color=s.C_PRIMARY,
                button_color=s.C_PRIMARY_H,
            )
            self._combo_metodo.grid(
                row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=4
            )

            # icono guardar pedido
            img_guardar = self._cargar_icono("check.png", size=(18, 18))

            self._btn(
                footer,
                "   GUARDAR PEDIDO",
                self._ped_guardar,
                color=s.C_GREEN,
                height=s.BTN_HEIGHT_LG,
                image=img_guardar,
                compound="left",
            ).grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 10))

        self._ped_cambiar_tab(self.tab_activa)

    def _ped_cambiar_tab(self, cat: str):
        self.tab_activa = cat
        for c, b in self._tab_btns.items():
            b.configure(
                fg_color=s.CAT_COLORS[c] if c == cat else ("#9ab8aa", "#2a4035")
            )
        self._ped_cargar_productos(categoria=cat)

    def _ped_filtrar_prod(self, event=None):
        txt = self._e_buscar_prod_pedido.get().strip()
        if txt:
            self._ped_cargar_productos(filtro=txt)
        else:
            self._ped_cambiar_tab(self.tab_activa)

    def _ped_cargar_productos(self, categoria=None, filtro=None):
        try:
            filas = db.obtener_productos(categoria=categoria, filtro=filtro)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        color = s.CAT_COLORS.get(categoria or self.tab_activa, s.C_BLUE)
        self._prod_grid.cargar(filas, color)

    def _ped_agregar(self, prod: tuple):
        id_p, nombre, precio = prod
        for p in self.carrito:
            if p["id"] == id_p:
                p["cantidad"] += 1
                p["subtotal"] = round(p["cantidad"] * p["precio"], 2)
                self._ped_refrescar_carrito()
                return
        self.carrito.append(
            {
                "id": id_p,
                "nombre": nombre,
                "precio": precio,
                "cantidad": 1,
                "subtotal": precio,
            }
        )
        self._ped_refrescar_carrito()

    def _ped_cambiar_cant(self, prod: dict, delta: int):
        for p in self.carrito:
            if p["id"] == prod["id"]:
                p["cantidad"] = max(0, p["cantidad"] + delta)
                if p["cantidad"] == 0:
                    self.carrito.remove(p)
                else:
                    p["subtotal"] = round(p["cantidad"] * p["precio"], 2)
                break
        self._ped_refrescar_carrito()

    def _ped_eliminar(self, prod: dict):
        self.carrito = [p for p in self.carrito if p["id"] != prod["id"]]
        self._ped_refrescar_carrito()

    def _ped_refrescar_carrito(self):
        for w in self._frame_carrito.winfo_children():
            w.destroy()
        total = 0.0
        for p in self.carrito:
            CarritoItem(
                self._frame_carrito,
                p,
                self.tasa_bcv,
                on_change=self._ped_cambiar_cant,
                on_delete=self._ped_eliminar,
            ).pack(fill="x", padx=4, pady=3)
            total += p["subtotal"]
        self._lbl_total_usd.configure(text=f"${total:.2f}")
        self._lbl_total_bs.configure(text=f"Bs. {total*self.tasa_bcv:,.0f}")

    def _ped_buscar_persona(self, event=None):
        for w in self._frame_res_persona.winfo_children():
            w.destroy()
        txt = self._e_persona.get().strip()
        if len(txt) < 2:
            return
        try:
            filas = db.buscar_personas(txt)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for f in filas:
            id_p, nom, ape, tipo, grado, id_c, ref, tel = f
            sub = tipo + (f" · {grado}" if grado else "")
            ctk.CTkButton(
                self._frame_res_persona,
                text=f"  {nom} {ape}  ·  {sub}  ·  {ref}",
                anchor="w",
                height=32,
                font=s.f_small(),
                fg_color=s.C_BG2,
                text_color=s.C_TEXT,
                hover_color=s.C_PRIMARY,
                corner_radius=8,
                command=lambda d=(
                    id_p,
                    f"{nom} {ape}",
                    id_c,
                    ref,
                ): self._ped_sel_persona(d),
            ).pack(fill="x", pady=2, padx=2)

    def _ped_sel_persona(self, data: tuple):
        id_p, nombre, id_c, ref = data
        self.persona_sel = {
            "id_persona": id_p,
            "nombre": nombre,
            "id_cuenta": id_c,
            "cuenta": ref,
        }
        self._lbl_persona.configure(
            text=f"✅  {nombre}  —  {ref}", text_color=s.C_GREEN
        )
        for w in self._frame_res_persona.winfo_children():
            w.destroy()
        self._e_persona.delete(0, "end")

    def _ped_guardar(self):
        if not self.carrito:
            messagebox.showwarning("Pedido vacío", "Agrega productos antes de guardar.")
            return
        if not self.persona_sel:
            messagebox.showwarning("Sin persona", "Selecciona quién hizo el pedido.")
            return
        metodo = self._combo_metodo.get()
        total = round(sum(p["subtotal"] for p in self.carrito), 2)
        try:
            db.registrar_pedido(
                self.persona_sel["id_persona"], self.carrito, self.tasa_bcv, metodo
            )
            estado = (
                "quedó PENDIENTE de pago"
                if metodo == "Crédito"
                else f"pagado en {metodo}"
            )
            messagebox.showinfo(
                "✅ Pedido Registrado",
                f"Alumno: {self.persona_sel['nombre']}\n"
                f"Cuenta: {self.persona_sel['cuenta']}\n\n"
                f"Total: ${total:.2f}\n"
                f"Este pedido {estado}.",
            )
            self.carrito = []
            self._ped_refrescar_carrito()
            self.persona_sel = None
            self._lbl_persona.configure(
                text="⚠️  Selecciona quién pide", text_color=s.C_ORANGE
            )
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    # ============================================================
    # MÓDULO: CUENTAS POR COBRAR
    # ============================================================

    def abrir_cobrar(self):
        container = self._mostrar_vista("cobrar")
        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=1)
            container.grid_columnconfigure(1, weight=1)
            container.grid_rowconfigure(0, weight=1)

            # ── IZQUIERDA: LISTA DE CUENTAS CON DEUDA ────────
            fl = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fl.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
            fl.grid_rowconfigure(1, weight=1)
            fl.grid_columnconfigure(0, weight=1)

            top = self._card(fl)
            top.pack(fill="x", pady=(0, 8))

            # icono de cuentas por cobrar y de enviar a todos
            img_cobrar = self._cargar_icono("tarjeta.png", size=(18, 18))
            img_cobrar_masivo = self._cargar_icono("enviaratodos.png", size=(18, 18))

            ctk.CTkLabel(
                top,
                text="   Cuentas por Cobrar",
                font=s.f_subtitulo(),
                text_color=s.C_TEXT,
                image=img_cobrar,
                compound="left",
            ).pack(pady=(12, 4), padx=14, anchor="w")
            self._lbl_cobrar_resumen = ctk.CTkLabel(
                top, text="", font=s.f_small(), text_color=s.C_SUBTEXT
            )
            self._lbl_cobrar_resumen.pack(pady=(0, 4), padx=14, anchor="w")
            self._btn(
                top,
                "   Enviar recordatorio a TODOS",
                self._cobrar_masivo,
                color=s.C_ORANGE,
                image=img_cobrar_masivo,
                compound="left",
            ).pack(fill="x", padx=14, pady=(4, 12))

            self._frame_cobrar_lista = ctk.CTkScrollableFrame(
                fl, fg_color="transparent", corner_radius=0
            )
            self._frame_cobrar_lista.pack(fill="both", expand=True)

            # ── DERECHA: DETALLE DE LA CUENTA SELECCIONADA ───
            fr = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fr.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
            fr.grid_rowconfigure(1, weight=1)
            fr.grid_columnconfigure(0, weight=1)

            # icono de seleccion una cuenta
            img_seleccionar = self._cargar_icono("tarjeta.png", size=(18, 18))

            self._lbl_cobrar_titulo = ctk.CTkLabel(
                fr,
                text="   Selecciona una cuenta",
                font=s.f_subtitulo(),
                text_color=s.C_SUBTEXT,
                image=img_seleccionar,
                compound="left",
            )
            self._lbl_cobrar_titulo.pack(pady=(16, 8))

            self._frame_cobrar_detalle = ctk.CTkScrollableFrame(
                fr, fg_color="transparent", corner_radius=0
            )
            self._frame_cobrar_detalle.pack(fill="both", expand=True, padx=4)

        self._cobrar_cargar_lista()

    def _cobrar_semaforo(self, deuda: float) -> tuple:
        """Retorna (emoji, color, etiqueta) según el monto de deuda."""
        if deuda <= 0:
            return "🟢", s.C_GREEN, "Sin deuda"
        elif deuda < 5:
            return "🟡", s.C_YELLOW, "Debe esta semana"
        elif deuda < 15:
            return "🟠", s.C_ORANGE, "Debe varias semanas"
        else:
            return "🔴", s.C_ACCENT, "Moroso"

    def _cobrar_cargar_lista(self):
        for w in self._frame_cobrar_lista.winfo_children():
            w.destroy()
        try:
            cuentas = db.obtener_cuentas_con_deuda()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        total_deuda = sum(float(c[4]) for c in cuentas)
        self._lbl_cobrar_resumen.configure(
            text=f"{len(cuentas)} cuentas con deuda  ·  Total: ${total_deuda:.2f}"
        )

        # emoji no hay ninguna cuenta con deuda pendiente
        img_no_deuda = self._cargar_icono("sindeuda.png", size=(32, 32))

        if not cuentas:
            ctk.CTkLabel(
                self._frame_cobrar_lista,
                text="   No hay ninguna cuenta con deuda pendiente.",
                font=s.f_normal(),
                text_color=s.C_GREEN,
                image=img_no_deuda,
                compound="left",
            ).pack(pady=30)
            return

        for c in cuentas:
            id_c, ref, tel, tipo, deuda = c
            deuda = float(deuda)
            emoji, color, etiqueta = self._cobrar_semaforo(deuda)

            card = self._card(self._frame_cobrar_lista)
            card.pack(fill="x", padx=4, pady=4)
            card.grid_columnconfigure(0, weight=1)

            r0 = ctk.CTkFrame(card, fg_color="transparent")
            r0.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
            r0.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                r0,
                text=f"{emoji}  {ref}",
                font=s.f_bold(),
                text_color=s.C_TEXT,
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                r0,
                text=f"${deuda:.2f}",
                font=ctk.CTkFont(family=s.FONT, size=15, weight="bold"),
                text_color=color,
            ).grid(row=0, column=1)

            ctk.CTkLabel(
                card, text=etiqueta, font=s.f_small(), text_color=color, anchor="w"
            ).grid(row=1, column=0, padx=12, pady=(0, 8), sticky="w")

            # Botón "Ver Detalle" para abrir la vista de detalle de la cuenta y whatsapp
            img_ver_detalle = self._cargar_icono("ojos.png", size=(18, 18))
            img_whatsapp = self._cargar_icono("whatsapp.png", size=(18, 18))

            self._btn(
                card,
                "   Ver Detalle",
                lambda i=id_c, r=ref, t=tel, d=deuda: self._cobrar_seleccionar(
                    i, r, t, d
                ),
                color=s.C_BLUE,
                image=img_ver_detalle,
                compound="left",
            ).grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

    def _cobrar_seleccionar(self, id_cuenta: int, ref: str, tel: str, deuda: float):

        img_titulo_cuenta = self._cargar_icono("tarjeta.png", size=(18, 18))

        self._lbl_cobrar_titulo.configure(
            text=f"   {ref}",
            image=img_titulo_cuenta,
            compound="left",
            text_color=s.C_TEXT,
        )
        for w in self._frame_cobrar_detalle.winfo_children():
            w.destroy()

        try:
            detalle = db.obtener_detalle_deuda_cuenta(id_cuenta)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        resumen = self._card(self._frame_cobrar_detalle)
        resumen.pack(fill="x", padx=4, pady=(0, 8))
        ctk.CTkLabel(
            resumen,
            text=f"Deuda total: ${deuda:.2f}",
            font=s.f_subtitulo(),
            text_color=s.C_ACCENT,
        ).pack(pady=12)
        self._btn(
            resumen,
            "   Generar Mensaje WhatsApp",
            lambda: self._cobrar_generar_whatsapp(ref, tel, detalle, deuda),
            color="#25D366",
            image=self._cargar_icono("whatsapp.png", size=(18, 18)),
            compound="left",
        ).pack(fill="x", padx=14, pady=(0, 12))

        if not detalle:
            ctk.CTkLabel(
                self._frame_cobrar_detalle,
                text="Sin pedidos pendientes de pago.",
                font=s.f_normal(),
                text_color=s.C_SUBTEXT,
            ).pack(pady=20)
            return

        ctk.CTkLabel(
            self._frame_cobrar_detalle,
            text="Detalle de pedidos:",
            font=s.f_bold(),
            text_color=s.C_TEXT,
        ).pack(anchor="w", padx=4, pady=(4, 4))

        for d in detalle:
            id_ped, persona, fecha, total, pagado, pendiente, estado = d
            total, pagado, pendiente = float(total), float(pagado), float(pendiente)
            card = self._card(self._frame_cobrar_detalle)
            card.pack(fill="x", padx=4, pady=3)
            card.grid_columnconfigure(0, weight=1)

            r0 = ctk.CTkFrame(card, fg_color="transparent")
            r0.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 1))
            r0.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                r0,
                text=f"{fmt_fecha_corta(fecha)} · {persona}",
                font=s.f_bold(),
                text_color=s.C_TEXT,
                anchor="w",
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                r0, text=f"${pendiente:.2f}", font=s.f_bold(), text_color=s.C_ACCENT
            ).grid(row=0, column=1)

            try:
                items = db.obtener_detalle_pedido(id_ped)
                items_txt = ", ".join(f"{i[0]} x{i[1]}" for i in items)
            except Exception:
                items_txt = ""
            ctk.CTkLabel(
                card,
                text=items_txt,
                font=s.f_small(),
                text_color=s.C_SUBTEXT,
                anchor="w",
                wraplength=340,
            ).grid(row=1, column=0, padx=12, pady=(0, 2), sticky="w")

            info_pago = f"Total ${total:.2f}"
            if pagado > 0:
                info_pago += f"  ·  Abonado ${pagado:.2f}  ({estado})"
            ctk.CTkLabel(
                card,
                text=info_pago,
                font=s.f_small(),
                text_color=s.C_GREEN if pagado > 0 else s.C_SUBTEXT,
                anchor="w",
            ).grid(row=2, column=0, padx=12, pady=(0, 4), sticky="w")

            # emoji de registrar pago y eliminar pedido
            img_registrar_pago = self._cargar_icono("bolsa_dinero.png", size=(18, 18))
            img_eliminar_pedido = self._cargar_icono("borrar.png", size=(18, 18))

            bf = ctk.CTkFrame(card, fg_color="transparent")
            bf.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 8))
            self._btn(
                bf,
                "  Registrar Pago",
                lambda i=id_ped, ic=id_cuenta, p=pendiente, r=ref: self._cobrar_abrir_pago(
                    i, ic, p, r
                ),
                color=s.C_GREEN,
                height=32,
                image=img_registrar_pago,
                compound="left",
            ).pack(side="left", padx=4)
            self._btn(
                bf,
                "  Eliminar Pedido",
                lambda i=id_ped, ic=id_cuenta, r=ref, t=tel: self._cobrar_eliminar_pedido(
                    i, ic, r, t
                ),
                color="#555",
                height=32,
                image=img_eliminar_pedido,
                compound="left",
            ).pack(side="left", padx=4)

    def _cobrar_abrir_pago(
        self, id_pedido: int, id_cuenta: int, pendiente: float, ref: str
    ):
        v = ctk.CTkToplevel(self)
        v.title("Registrar Pago")
        v.geometry("380x260")
        v.grab_set()
        ctk.CTkLabel(v, text=f"Registrar Pago — {ref}", font=s.f_subtitulo()).pack(
            pady=(18, 4)
        )
        ctk.CTkLabel(
            v,
            text=f"Pendiente: ${pendiente:.2f}",
            font=s.f_bold(),
            text_color=s.C_ACCENT,
        ).pack(pady=(0, 10))

        e_monto = self._entry(v, ph=f"Monto (máx ${pendiente:.2f})")
        e_monto.insert(0, f"{pendiente:.2f}")
        e_monto.pack(pady=6, padx=24, fill="x")

        m_met = self._opt(
            v, ["Efectivo $", "Efectivo Bs", "Pago Móvil", "Transferencia"]
        )
        m_met.pack(pady=6, padx=24, fill="x")

        def confirmar():
            try:
                monto = float(e_monto.get().strip())
                if monto <= 0 or monto > pendiente + 0.01:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Error",
                    f"Monto inválido. Debe ser entre 0 y ${pendiente:.2f}",
                    parent=v,
                )
                return
            try:
                db.registrar_pago(
                    id_pedido, id_cuenta, monto, self.tasa_bcv, m_met.get()
                )
                messagebox.showinfo("✅", f"Pago de ${monto:.2f} registrado.", parent=v)
                v.destroy()
                self._cobrar_cargar_lista()
                self._lbl_cobrar_titulo.configure(
                    text="👈  Selecciona una cuenta", text_color=s.C_SUBTEXT
                )
                for w in self._frame_cobrar_detalle.winfo_children():
                    w.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=v)

        self._btn(v, "✅  Confirmar Pago", confirmar, color=s.C_GREEN).pack(
            pady=16, padx=24, fill="x"
        )

    def _cobrar_eliminar_pedido(
        self, id_pedido: int, id_cuenta: int, ref: str, tel: str
    ):
        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar este pedido completo?\nEsta acción no se puede deshacer.",
        ):
            return
        try:
            db.eliminar_pedido(id_pedido)
            messagebox.showinfo("✅", "Pedido eliminado.")
            self._cobrar_cargar_lista()
            self._lbl_cobrar_titulo.configure(
                text="👈  Selecciona una cuenta", text_color=s.C_SUBTEXT
            )
            for w in self._frame_cobrar_detalle.winfo_children():
                w.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cobrar_generar_whatsapp(self, ref: str, tel: str, detalle: list, deuda: float):
        lineas = []
        for d in detalle:
            id_ped, persona, fecha, total, pagado, pendiente, estado = d
            try:
                items = db.obtener_detalle_pedido(id_ped)
                items_txt = ", ".join(f"{i[0]} x{i[1]}" for i in items)
            except Exception:
                items_txt = "pedido"
            lineas.append(
                f"• {fmt_fecha_corta(fecha)}: {items_txt} — ${float(pendiente):.2f}"
            )

        detalle_txt = "\n".join(lineas) if lineas else "Sin pedidos pendientes."
        mensaje = (
            f"Hola, buenos días. Le saluda la Cantina Escolar R.R. 🍽️\n\n"
            f"Le informamos el consumo pendiente de pago de *{ref}*:\n\n"
            f"{detalle_txt}\n\n"
            f"💰 Total pendiente: *${deuda:.2f}*\n\n"
            f"Agradecemos su colaboración para cancelar el pago.\n"
            f"¡Muchas gracias!"
        )
        wa_abrir_link(tel, mensaje)

    def _cobrar_masivo(self):
        try:
            cuentas = db.obtener_cuentas_con_deuda()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if not cuentas:
            messagebox.showinfo("Sin deudas", "No hay cuentas con deuda pendiente.")
            return
        if not messagebox.askyesno(
            "Confirmar envío masivo",
            f"Se abrirán {len(cuentas)} pestañas de WhatsApp, una por cada "
            f"cuenta con deuda. ¿Continuar?",
        ):
            return
        for c in cuentas:
            id_c, ref, tel, tipo, deuda = c
            try:
                detalle = db.obtener_detalle_deuda_cuenta(id_c)
                self._cobrar_generar_whatsapp(ref, tel, detalle, float(deuda))
            except Exception:
                continue

    # ============================================================
    # MÓDULO: PRODUCTOS
    # ============================================================

    def abrir_productos(self):
        container = self._mostrar_vista("productos")
        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=1)
            container.grid_rowconfigure(0, weight=0)
            container.grid_rowconfigure(1, weight=0)  # tabs categoría
            container.grid_rowconfigure(2, weight=1)  # grid productos

            # Formulario de nuevo producto
            top = self._card(container)
            top.grid(row=0, column=0, sticky="ew", padx=10, pady=(4, 4))
            top.grid_columnconfigure(0, weight=1)

            # icono de gestión de productos de hamburguesa y de guardar
            img_gestion_prod = self._cargar_icono("hamburguesa.png", size=(18, 18))
            img_guardar_prod = self._cargar_icono("guardar.png", size=(18, 18))

            ctk.CTkLabel(
                top,
                text="   Gestión de Productos",
                font=s.f_subtitulo(),
                text_color=s.C_TEXT,
                image=img_gestion_prod,
                compound="left",
            ).grid(row=0, column=0, columnspan=5, pady=(8, 4))

            self._e_nom_p = self._entry(top, ph="Nombre del producto")
            self._e_nom_p.grid(row=1, column=0, sticky="ew", padx=8, pady=6)

            self._m_cat_p = self._opt(top, s.CATEGORIAS)
            self._m_cat_p.grid(row=1, column=1, padx=6, pady=6)

            self._e_precio_p = self._entry(top, ph="Precio $", width=100)
            self._e_precio_p.grid(row=1, column=2, padx=6, pady=6)

            self._btn(
                top,
                "   Guardar",
                self._prod_guardar,
                image=img_guardar_prod,
                compound="left",
                color=s.C_GREEN,
            ).grid(row=1, column=3, padx=6, pady=6)

            self._e_buscar_prod_gestion = self._entry(top, ph="🔍 Filtrar...")
            self._e_buscar_prod_gestion.grid(row=1, column=4, padx=6, pady=6)
            self._e_buscar_prod_gestion.bind(
                "<KeyRelease>",
                lambda e: self._prod_cargar(self._e_buscar_prod_gestion.get().strip()),
            )

            # Tabs por categoría — muestra solo una a la vez (más rápido)
            tabs_p = ctk.CTkFrame(container, fg_color="transparent")
            tabs_p.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 4))
            self._prod_tab_activa = s.CATEGORIAS[0]
            self._prod_tab_btns = {}
            for cat in s.CATEGORIAS:
                b = ctk.CTkButton(
                    tabs_p,
                    text=cat,
                    height=32,
                    font=s.f_small_bold(),
                    fg_color=s.CAT_COLORS[cat],
                    hover_color=s.hover(s.CAT_COLORS[cat]),
                    corner_radius=18,
                    command=lambda c=cat: self._prod_cambiar_tab(c),
                )
                b.pack(side="left", padx=4)
                self._prod_tab_btns[cat] = b

            self._frame_prods = ctk.CTkScrollableFrame(
                container, fg_color="transparent", corner_radius=0
            )
            self._frame_prods.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 6))

        self._prod_cambiar_tab(
            self._prod_tab_activa
            if hasattr(self, "_prod_tab_activa")
            else s.CATEGORIAS[0]
        )

    def _prod_cambiar_tab(self, cat: str):
        """Carga solo la categoría seleccionada — evita renderizar 73 cards de golpe."""
        self._prod_tab_activa = cat
        if hasattr(self, "_prod_tab_btns"):
            for c, b in self._prod_tab_btns.items():
                b.configure(
                    fg_color=s.CAT_COLORS[c] if c == cat else ("#9ab8aa", "#2a4035")
                )
        filtro = (
            self._e_buscar_prod_gestion.get().strip()
            if hasattr(self, "_e_buscar_prod_gestion")
            else ""
        )
        self._prod_cargar(filtro=filtro, categoria=cat)

    def _prod_guardar(self):
        nombre = self._e_nom_p.get().strip()
        cat = self._m_cat_p.get()
        precio = self._e_precio_p.get().strip()
        if not nombre or not precio:
            messagebox.showwarning("Atención", "Nombre y precio son obligatorios.")
            return
        try:
            pval = float(precio)
        except ValueError:
            messagebox.showerror("Error", "Precio inválido.")
            return
        try:
            db.guardar_producto(nombre, cat, pval)
            messagebox.showinfo("✅", f"'{nombre}' guardado.")
            self._e_nom_p.delete(0, "end")
            self._e_precio_p.delete(0, "end")
            self._prod_cargar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _prod_cargar(self, filtro: str = "", categoria: str = None):
        for w in self._frame_prods.winfo_children():
            w.destroy()
        try:
            categorias = db.obtener_todos_productos()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        cat_activa = categoria or (
            self._prod_tab_activa if hasattr(self, "_prod_tab_activa") else None
        )

        img_disponible = self._cargar_icono("check.png", size=(18, 18))
        img_agotado = self._cargar_icono("cruz.png", size=(18, 18))
        img_editar = self._cargar_icono("lapiz.png", size=(18, 18))
        img_borrar = self._cargar_icono("borrar.png", size=(18, 18))

        for cat, prods in categorias.items():
            # Solo renderizar la categoría activa (salvo cuando hay filtro de texto)
            if not filtro and cat_activa and cat != cat_activa:
                continue
            if filtro:
                prods = [p for p in prods if filtro.lower() in p[1].lower()]
            if not prods:
                continue

            color = s.CAT_COLORS.get(cat, s.C_BLUE)
            ctk.CTkLabel(
                self._frame_prods,
                text=f"  {cat}",
                font=s.f_bold(),
                text_color=color,
                anchor="w",
            ).pack(fill="x", padx=6, pady=(10, 2))

            grid = ctk.CTkFrame(self._frame_prods, fg_color="transparent")
            grid.pack(fill="x", padx=4)
            cols = 4

            for i, (id_p, nom, _, precio, estado) in enumerate(prods):
                p = float(precio)
                disp = estado == "Disponible"

                # Borde en color de categoría → diferencia visual inmediata
                card = self._card(grid, border_width=2, border_color=color)
                card.grid(row=i // cols, column=i % cols, padx=6, pady=6, sticky="ew")
                card.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    card,
                    text=nom,
                    font=s.f_bold(),
                    text_color=s.C_TEXT if disp else s.C_SUBTEXT,
                    anchor="w",
                ).grid(row=0, column=0, padx=10, pady=(8, 1), sticky="w")
                ctk.CTkLabel(
                    card,
                    text=f"${p:.2f}  ·  Bs.{p*self.tasa_bcv:,.0f}",
                    font=s.f_small(),
                    text_color=color,
                    anchor="w",
                ).grid(row=1, column=0, padx=10, pady=(0, 3), sticky="w")

                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.grid(row=2, column=0, padx=6, pady=(0, 6), sticky="ew")
                btn_row.grid_columnconfigure(0, weight=1)
                btn_row.grid_columnconfigure(1, weight=0)
                btn_row.grid_columnconfigure(2, weight=0)

                self._btn(
                    btn_row,
                    "  Disp." if disp else "  Agotado",
                    lambda i=id_p, d=disp: self._prod_toggle(i, d),
                    color=s.C_SUCCESS if disp else "#7a9a8a",
                    height=26,
                    image=img_disponible if disp else img_agotado,
                ).grid(row=0, column=0, sticky="ew", padx=(0, 3))

                self._btn(
                    btn_row,
                    "",
                    lambda d=(id_p, nom, cat, p, estado): self._prod_editar(d),
                    color=("#6a8a78", "#3a5545"),
                    height=26,
                    width=34,
                    image=img_editar,
                ).grid(row=0, column=1, padx=(0, 3))

                self._btn(
                    btn_row,
                    "",
                    lambda i=id_p, n=nom: self._prod_eliminar(i, n),
                    color=s.C_DANGER,
                    height=26,
                    width=34,
                    image=img_borrar,
                ).grid(row=0, column=2)
            for c in range(cols):
                grid.grid_columnconfigure(c, weight=1)

    def _prod_toggle(self, id_prod: int, disponible: bool):
        try:
            db.toggle_estado_producto(id_prod, disponible)
            filtro = (
                self._e_buscar_prod_gestion.get().strip()
                if hasattr(self, "_e_buscar_prod_gestion")
                else ""
            )
            self._prod_cargar(filtro)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _prod_eliminar(self, id_prod: int, nombre: str):
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar '{nombre}' del catálogo permanentemente?\n"
            "Esta acción no se puede deshacer.",
        ):
            return
        try:
            db.eliminar_producto(id_prod)
            messagebox.showinfo("✅", f"'{nombre}' eliminado del catálogo.")
            self._prod_cargar(categoria=self._prod_tab_activa)
        except Exception as e:
            messagebox.showerror("Error al eliminar", str(e))

    def _prod_editar(self, datos: tuple):
        id_p, nom, cat, precio, estado = datos
        v = ctk.CTkToplevel(self)
        v.title("Editar Producto")
        v.geometry("420x380")
        v.grab_set()

        # titulo de la ventana con icono de editar
        img_editar_titulo = self._cargar_icono("lapiz.png", size=(24, 24))
        ctk.CTkLabel(
            v,
            text="✏️  Editar Producto",
            font=s.f_subtitulo(),
            image=img_editar_titulo,
            compound="left",
        ).pack(pady=(18, 8))
        e_nom = self._entry(v, ph="Nombre")
        e_nom.insert(0, nom)
        e_nom.pack(pady=5, padx=24, fill="x")
        m_cat = self._opt(v, s.CATEGORIAS)
        m_cat.set(cat)
        m_cat.pack(pady=5, padx=24, fill="x")
        e_precio = self._entry(v, ph="Precio $")
        e_precio.insert(0, str(precio))
        e_precio.pack(pady=5, padx=24, fill="x")
        m_est = self._opt(v, ["Disponible", "Agotado"])
        m_est.set(estado)
        m_est.pack(pady=5, padx=24, fill="x")

        def guardar():
            nuevo_nom = e_nom.get().strip()
            if not nuevo_nom:
                messagebox.showwarning(
                    "Atención", "El nombre es obligatorio.", parent=v
                )
                return
            try:
                nuevo_precio = float(e_precio.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Precio inválido.", parent=v)
                return
            try:
                db.actualizar_producto(
                    id_p, nuevo_nom, m_cat.get(), nuevo_precio, m_est.get()
                )
                messagebox.showinfo("✅", "Producto actualizado.", parent=v)
                filtro = (
                    self._e_buscar_prod_gestion.get().strip()
                    if hasattr(self, "_e_buscar_prod_gestion")
                    else ""
                )
                self._prod_cargar(filtro)
                v.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=v)

        img_guardar = self._cargar_icono("guardar.png", size=(18, 18))

        self._btn(v, "   Guardar", guardar, color=s.C_GREEN, image=img_guardar).pack(
            pady=14, padx=24, fill="x"
        )


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()
