"""
main.py
=======
Interfaz gráfica - Sistema de Gestión Cantina R.R.
NO contiene lógica de base de datos (ver database.py)
NO contiene estilos (ver styles.py)
"""

import os
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from datetime import date, datetime
import database as db
import styles as s

s.aplicar_tema()


# ============================================================
# COMPONENTES REUTILIZABLES
# ============================================================

class ProductoGrid(ctk.CTkScrollableFrame):
    """Grid de botones de productos. Al hacer clic llama on_click(id, nombre, precio)."""

    def __init__(self, master, on_click, **kwargs):
        super().__init__(master, **kwargs)
        self._on_click = on_click
        self._btns     = []
        self._cols     = 3

    def cargar(self, productos: list, color: str):
        """Recibe lista de (id, nombre, precio_usd) y dibuja botones."""
        for b in self._btns:
            b.destroy()
        self._btns = []
        for i, (id_p, nombre, precio_usd) in enumerate(productos):
            precio = float(precio_usd)   # MySQL devuelve Decimal, convertimos
            b = ctk.CTkButton(
                self,
                text=f"{nombre}\n${precio:.2f}",
                width=140, height=70,
                font=s.f_bold(),
                fg_color=color,
                hover_color=s.hover(color),
                corner_radius=12,
                command=lambda p=(id_p, nombre, precio): self._on_click(p)
            )
            b.grid(row=i // self._cols, column=i % self._cols,
                   padx=5, pady=5, sticky="ew")
            self._btns.append(b)
        for c in range(self._cols):
            self.grid_columnconfigure(c, weight=1)


class CarritoItem(ctk.CTkFrame):
    """Una fila del carrito con controles + / - / eliminar."""

    def __init__(self, master, producto: dict, tasa: float,
                 on_change, on_delete, **kwargs):
        super().__init__(master, corner_radius=10,
                         fg_color=s.C_CARD, **kwargs)
        self._p         = producto
        self._tasa      = tasa
        self._on_change = on_change
        self._on_delete = on_delete
        self._render()

    def _render(self):
        for w in self.winfo_children():
            w.destroy()
        self.grid_columnconfigure(0, weight=1)
        p = self._p

        # Nombre del producto
        ctk.CTkLabel(self, text=p["nombre"],
                     font=s.f_bold(), text_color=s.C_TEXT, anchor="w"
                     ).grid(row=0, column=0, padx=10, pady=(8, 1), sticky="w")

        # Subtotal en $ y Bs.
        ctk.CTkLabel(
            self,
            text=f"${p['subtotal']:.2f}  ·  Bs.{p['subtotal'] * self._tasa:,.0f}",
            font=s.f_small(), text_color=s.C_GREEN
        ).grid(row=1, column=0, padx=10, pady=(0, 6), sticky="w")

        # Controles cantidad
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=0, column=1, rowspan=2, padx=8, pady=4, sticky="e")

        ctk.CTkButton(
            ctrl, text="−", width=30, height=30,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=s.C_ORANGE, hover_color=s.hover(s.C_ORANGE),
            corner_radius=8,
            command=lambda: self._on_change(self._p, -1)
        ).pack(side="left", padx=2)

        ctk.CTkLabel(
            ctrl, text=str(p["cantidad"]),
            font=ctk.CTkFont(size=15, weight="bold"),
            width=28, text_color=s.C_TEXT
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            ctrl, text="+", width=30, height=30,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=s.C_GREEN, hover_color=s.hover(s.C_GREEN),
            corner_radius=8,
            command=lambda: self._on_change(self._p, +1)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            ctrl, text="🗑", width=30, height=30,
            font=ctk.CTkFont(size=13),
            fg_color=s.C_ACCENT, hover_color=s.hover(s.C_ACCENT),
            corner_radius=8,
            command=lambda: self._on_delete(self._p)
        ).pack(side="left", padx=(6, 2))


# ============================================================
# UTILIDADES
# ============================================================

def fmt_fecha(valor) -> str:
    """Convierte datetime o string a DD/MM/YYYY HH:MM legible."""
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    return str(valor) if valor else "—"


# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión — Cantina R.R.")
        self.geometry("1200x720")
        self.configure(fg_color=s.C_BG)

        # Estado global
        self.tasa_bcv:             float = 1.0
        self.tasa_fecha:           str   = "—"
        self.carrito:              list  = []
        self.persona_seleccionada: dict  = None
        self.tab_activa:           str   = "Por Unidad"
        self._cuenta_sel_id:       int   = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Registro y persistencia de pantallas en caché (Evita lentitud y parpadeos)
        self.home = ctk.CTkFrame(self, corner_radius=0, fg_color=s.C_BG)
        self.home.grid(row=0, column=1, sticky="nsew")
        self.home.grid_columnconfigure(0, weight=1)
        self.home.grid_rowconfigure(0, weight=1)

        self.views = {}

        self._build_nav()
        self._build_inicial_home()
        self._inicializar_tasa()

    def _mostrar_vista(self, nombre_vista: str):
        """Oculta las vistas existentes y despliega el frame seleccionado sin destruirlo."""
        for v in self.views.values():
            if v:
                v.grid_forget()
        
        if self.views.get(nombre_vista) is None:
            self.views[nombre_vista] = ctk.CTkFrame(self.home, corner_radius=0, fg_color="transparent")
            
        self.views[nombre_vista].grid(row=0, column=0, sticky="nsew")
        self.views[nombre_vista].grid_columnconfigure(0, weight=1)
        self.views[nombre_vista].grid_rowconfigure(0, weight=1)
        return self.views[nombre_vista]

    # ── HELPERS DE WIDGETS ───────────────────────────────────

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, corner_radius=s.CORNER_CARD,
                            fg_color=s.C_CARD, **kw)

    def _btn(self, parent, texto, cmd, color=None, height=None, **kw):
        color  = color  or s.C_BLUE
        height = height or s.BTN_HEIGHT
        return ctk.CTkButton(
            parent, text=texto,
            fg_color=color, hover_color=s.hover(color),
            font=s.f_bold(), height=height,
            corner_radius=s.CORNER,
            command=cmd, **kw)

    def _entry(self, parent, ph="", **kw):
        return ctk.CTkEntry(
            parent, placeholder_text=ph,
            font=s.f_normal(), height=s.BTN_HEIGHT,
            corner_radius=s.CORNER, **kw)

    def _opt(self, parent, values, **kw):
        return ctk.CTkOptionMenu(
            parent, values=values,
            font=s.f_normal(), height=s.BTN_HEIGHT,
            corner_radius=s.CORNER, **kw)

    # ── TASA BCV ─────────────────────────────────────────────

    def _inicializar_tasa(self):
        try:
            resultado = db.obtener_tasa_bcv_online()
            db.guardar_tasa_bcv(resultado["tasa"], date.today().strftime("%Y-%m-%d"))
            self.tasa_bcv   = resultado["tasa"]
            self.tasa_fecha = resultado["fecha"]
            self._actualizar_label_tasa()
        except Exception:
            self._cargar_tasa_desde_bd(silencioso=True)

    def _cargar_tasa_desde_bd(self, silencioso=False):
        try:
            resultado       = db.obtener_tasa_bcv()
            self.tasa_bcv   = resultado["tasa"]
            self.tasa_fecha = resultado["fecha"]
            self._actualizar_label_tasa()
            if not silencioso:
                messagebox.showinfo(
                    "Tasa cargada desde BD",
                    f"No hay internet. Se usó la tasa guardada:\n"
                    f"Bs. {self.tasa_bcv:,.2f}  —  {self.tasa_fecha}")
        except Exception as e:
            messagebox.showwarning(
                "Sin tasa BCV",
                f"No se pudo cargar la tasa BCV.\nIngresa la tasa manualmente.\n\nDetalle: {e}")

    def _actualizar_tasa_manual(self):
        val = simpledialog.askstring(
            "Tasa BCV Manual",
            f"Ingresa la tasa BCV de hoy ({date.today().strftime('%d/%m/%Y')}):",
            parent=self)
        if not val:
            return
        try:
            tasa = float(val.replace(",", "."))
            if tasa <= 0:
                raise ValueError
            db.guardar_tasa_bcv(tasa, date.today().strftime("%Y-%m-%d"))
            self.tasa_bcv   = tasa
            self.tasa_fecha = date.today().strftime("%d/%m/%Y")
            self._actualizar_label_tasa()
            self._pos_refrescar_carrito()
            messagebox.showinfo("✅", f"Tasa actualizada: Bs. {tasa:,.2f}")
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número válido.")

    def _actualizar_tasa_online(self):
        try:
            resultado = db.obtener_tasa_bcv_online()
            db.guardar_tasa_bcv(resultado["tasa"], date.today().strftime("%Y-%m-%d"))
            self.tasa_bcv   = resultado["tasa"]
            self.tasa_fecha = resultado["fecha"]
            self._actualizar_label_tasa()
            self._pos_refrescar_carrito()
            messagebox.showinfo(
                "✅ Tasa actualizada",
                f"Tasa BCV: Bs. {self.tasa_bcv:,.2f}\nFecha: {self.tasa_fecha}")
        except Exception as e:
            messagebox.showwarning(
                "Sin conexión",
                f"No se pudo obtener la tasa online.\n\n{e}\n\nPuedes ingresarla manualmente.")

    def _actualizar_label_tasa(self):
        if hasattr(self, "_lbl_tasa"):
            self._lbl_tasa.configure(text=f"Bs. {self.tasa_bcv:,.2f}\n{self.tasa_fecha}")

    # ── NAVEGACIÓN ───────────────────────────────────────────

    def _build_nav(self):
        nav = ctk.CTkFrame(self, corner_radius=0, fg_color=s.C_NAV, width=220)
        nav.grid(row=0, column=0, sticky="nsew")
        nav.grid_propagate(False)
        nav.grid_rowconfigure(8, weight=1)

        # Diseño del logo institucional adaptativo con ruta absoluta
        try:
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_logo = os.path.join(directorio_actual, "assets", "logo.png") # Cambia a "assets", "logo.png" si creas la carpeta
            
            logo_img = ctk.CTkImage(Image.open(ruta_logo), size=(80, 80))
            ctk.CTkLabel(nav, image=logo_img, text="").grid(row=0, column=0, pady=(24, 4))
        except Exception:
            ctk.CTkLabel(nav, text="🍽️", font=ctk.CTkFont(size=34)).grid(row=0, column=0, pady=(24, 2))

        ctk.CTkLabel(nav, text="CANTINA R.R.",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="white"
                     ).grid(row=1, column=0, pady=(0, 12))

        # Panel visual unificado para la visualización del dólar oficial
        bcv_panel = ctk.CTkFrame(nav, corner_radius=10, fg_color="#1e2547")
        bcv_panel.grid(row=2, column=0, padx=14, pady=(0, 16), sticky="ew")

        self._lbl_tasa = ctk.CTkLabel(
            bcv_panel, text="Cargando tasa...",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=s.C_GREEN)
        self._lbl_tasa.pack(pady=(8, 4))

        ctk.CTkButton(
            bcv_panel, text="🔄 Actualizar Tasa", height=28, font=ctk.CTkFont(size=11),
            fg_color="#2d3561", hover_color="#3d4a8a", command=self._actualizar_tasa_online
        ).pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkButton(
            bcv_panel, text="✏️ Tasa Manual", height=28, font=ctk.CTkFont(size=11),
            fg_color="#2d3561", hover_color="#3d4a8a", command=self._actualizar_tasa_manual
        ).pack(fill="x", padx=10, pady=(0, 10))

        # Modulos de cambio de pantalla principal
        for icono, texto, cmd, fila in [
            ("🛒", "Punto de Venta",     self.abrir_pos,       4),
            ("👥", "Cuentas",           self.abrir_cuentas,   5),
            ("📋", "Historial",         self.abrir_historial, 6),
            ("🍔", "Productos",         self.abrir_productos, 7),
        ]:
            f = ctk.CTkFrame(nav, fg_color="transparent", cursor="hand2")
            f.grid(row=fila, column=0, sticky="ew", padx=10, pady=3)
            f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(f, text=icono, font=ctk.CTkFont(size=18), width=36
                         ).grid(row=0, column=0, padx=(10, 4))
            ctk.CTkLabel(f, text=texto, font=s.f_nav(), text_color="white", anchor="w"
                         ).grid(row=0, column=1, sticky="ew")
            for w in [f] + list(f.winfo_children()):
                w.bind("<Button-1>", lambda e, c=cmd: c())
                w.bind("<Enter>",    lambda e, fr=f: fr.configure(fg_color=("#2d3561","#2d3561")))
                w.bind("<Leave>",    lambda e, fr=f: fr.configure(fg_color="transparent"))

        self._opt(nav, ["Dark", "Light", "System"],
                  fg_color="#2d3561", button_color="#3d4a8a",
                  command=lambda m: ctk.set_appearance_mode(m)
                  ).grid(row=9, column=0, padx=16, pady=20, sticky="ew")

    def _build_inicial_home(self):
        container = self._mostrar_vista("home")
        welcome_frame = ctk.CTkFrame(container, fg_color="transparent")
        welcome_frame.pack(expand=True)
        ctk.CTkLabel(welcome_frame, text="Bienvenido 👋",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=s.C_TEXT).pack(pady=(0, 10))
        ctk.CTkLabel(welcome_frame, text="Sistema de Gestión — Cantina Escolar R.R.",
                     font=s.f_normal(), text_color=s.C_SUBTEXT).pack()

    # ============================================================
    # MÓDULO: PUNTO DE VENTA
    # ============================================================

    def abrir_pos(self):
        container = self._mostrar_vista("pos")
        
        # Re-inicialización estructural limpia si no existe el contenedor interno
        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=3)
            container.grid_columnconfigure(1, weight=2)
            
            # ── IZQUIERDA: CATÁLOGO ──────────────────────────────
            fl = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fl.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
            fl.grid_rowconfigure(2, weight=1)
            fl.grid_columnconfigure(0, weight=1)

            self._e_buscar_prod = self._entry(fl, ph="🔍  Buscar producto...")
            self._e_buscar_prod.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
            self._e_buscar_prod.bind("<KeyRelease>", self._pos_filtrar)

            tabs = ctk.CTkFrame(fl, fg_color="transparent")
            tabs.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 6))
            self._tab_btns = {}
            for cat in s.CATEGORIAS:
                b = ctk.CTkButton(
                    tabs, text=cat, height=34, font=ctk.CTkFont(size=12, weight="bold"),
                    fg_color=s.CAT_COLORS[cat], hover_color=s.hover(s.CAT_COLORS[cat]),
                    corner_radius=18, command=lambda c=cat: self._pos_cambiar_tab(c))
                b.pack(side="left", padx=4)
                self._tab_btns[cat] = b

            self._prod_grid = ProductoGrid(fl, on_click=self._pos_agregar, fg_color="transparent", corner_radius=0)
            self._prod_grid.grid(row=2, column=0, sticky="nsew", padx=4)

            # ── DERECHA: PERSONA DINÁMICA + CARRITO ────────────
            fr = ctk.CTkFrame(container, corner_radius=0, fg_color=("#e8e8f0", "#0f0f1a"))
            fr.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
            fr.grid_columnconfigure(0, weight=1)
            fr.grid_rowconfigure(0, weight=0)
            fr.grid_rowconfigure(2, weight=1)

            top_r = self._card(fr)
            top_r.grid(row=0, column=0, sticky="ew", padx=10, pady=(4, 2))
            top_r.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(top_r, text="¿Quién compra?", font=s.f_bold(), text_color=s.C_TEXT
                         ).grid(row=0, column=0, pady=(4, 0), padx=12, sticky="w")

            self._e_persona = self._entry(top_r, ph="🔍  Nombre del cliente...")
            self._e_persona.grid(row=1, column=0, sticky="ew", padx=10, pady=2)
            self._e_persona.bind("<KeyRelease>", self._pos_buscar_persona)

            self._frame_res_persona = ctk.CTkScrollableFrame(top_r, height=110, fg_color="transparent")
            self._frame_res_persona.grid_forget()

            self._lbl_persona = ctk.CTkLabel(top_r, text="⚠️  Selecciona quién compra",
                                             font=ctk.CTkFont(size=11, weight="bold"), text_color=s.C_ORANGE)
            self._lbl_persona.grid(row=3, column=0, pady=(2, 4), padx=12)

            ctk.CTkLabel(fr, text="🛒  Carrito", font=s.f_subtitulo(), text_color=s.C_TEXT
                         ).grid(row=1, column=0, pady=(6, 2), padx=14, sticky="w")

            self._frame_carrito = ctk.CTkScrollableFrame(fr, fg_color="transparent", corner_radius=0)
            self._frame_carrito.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 4))
            self._frame_carrito.grid_columnconfigure(0, weight=1)

            footer = self._card(fr)
            footer.grid(row=3, column=0, sticky="ew", padx=10, pady=(4, 6))
            footer.grid_columnconfigure(0, weight=1)
            footer.grid_columnconfigure(1, weight=1)

            self._lbl_total_usd = ctk.CTkLabel(footer, text="$0.00", font=s.f_total(), text_color=s.C_GREEN)
            self._lbl_total_usd.grid(row=0, column=0, columnspan=2, pady=(10, 2))

            self._lbl_total_bs = ctk.CTkLabel(footer, text="Bs. 0", font=s.f_normal(), text_color=s.C_YELLOW)
            self._lbl_total_bs.grid(row=1, column=0, columnspan=2, pady=(0, 6))

            self._combo_metodo = self._opt(footer, s.METODOS_PAGO, fg_color=s.C_BLUE, button_color=s.hover(s.C_BLUE))
            self._combo_metodo.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

            self._btn(footer, "✅  FINALIZAR VENTA", self._pos_finalizar, color=s.C_GREEN, height=s.BTN_HEIGHT_LG
                      ).grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 12))

            self._pos_cambiar_tab("Por Unidad")
            
        # Refrescar datos del carrito e interfaz
        self._pos_refrescar_carrito()

    def _pos_cambiar_tab(self, cat: str):
        self.tab_activa = cat
        for c, b in self._tab_btns.items():
            b.configure(fg_color=s.CAT_COLORS[c] if c == cat else ("#aaa", "#3a3a5c"))
        self._pos_cargar_productos(categoria=cat)

    def _pos_filtrar(self, event=None):
        txt = self._e_buscar_prod.get().strip()
        if txt:
            self._pos_cargar_productos(filtro=txt)
        else:
            self._pos_cambiar_tab(self.tab_activa)

    def _pos_cargar_productos(self, categoria: str = None, filtro: str = None):
        try:
            filas = db.obtener_productos(categoria=categoria, filtro=filtro)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        color = s.CAT_COLORS.get(categoria or self.tab_activa, s.C_BLUE)
        self._prod_grid.cargar(filas, color)

    def _pos_agregar(self, prod: tuple):
        id_p, nombre, precio = prod
        for p in self.carrito:
            if p["id"] == id_p:
                p["cantidad"] += 1
                p["subtotal"] = round(p["cantidad"] * p["precio"], 2)
                self._pos_refrescar_carrito()
                return
        self.carrito.append({
            "id": id_p, "nombre": nombre,
            "precio": precio, "cantidad": 1, "subtotal": precio
        })
        self._pos_refrescar_carrito()

    def _pos_cambiar_cant(self, prod: dict, delta: int):
        for p in self.carrito:
            if p["id"] == prod["id"]:
                p["cantidad"] = max(0, p["cantidad"] + delta)
                if p["cantidad"] == 0:
                    self.carrito.remove(p)
                else:
                    p["subtotal"] = round(p["cantidad"] * p["precio"], 2)
                break
        self._pos_refrescar_carrito()

    def _pos_eliminar(self, prod: dict):
        self.carrito = [p for p in self.carrito if p["id"] != prod["id"]]
        self._pos_refrescar_carrito()

    def _pos_refrescar_carrito(self):
        if not hasattr(self, "_frame_carrito"):
            return
        for w in self._frame_carrito.winfo_children():
            w.destroy()
        total = 0.0
        for p in self.carrito:
            CarritoItem(
                self._frame_carrito, p, self.tasa_bcv,
                on_change=self._pos_cambiar_cant,
                on_delete=self._pos_eliminar
            ).pack(fill="x", padx=4, pady=3)
            total += p["subtotal"]
        self._lbl_total_usd.configure(text=f"${total:.2f}")
        self._lbl_total_bs.configure(text=f"Bs. {total * self.tasa_bcv:,.0f}")

    def _pos_buscar_persona(self, event=None):
        for w in self._frame_res_persona.winfo_children():
            w.destroy()
        txt = self._e_persona.get().strip()
        if len(txt) < 2:
            self._frame_res_persona.grid_forget()
            return
        try:
            filas = db.buscar_personas(txt)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if not filas:
            self._frame_res_persona.grid_forget()
            return

        self._frame_res_persona.grid(row=2, column=0, sticky="ew", padx=10, pady=3)
        for f in filas:
            id_p, nom, ape, tipo, id_c, ref = f
            ctk.CTkButton(
                self._frame_res_persona, text=f"  {nom} {ape}  ·  {tipo}  ·  {ref}",
                anchor="w", height=32, font=s.f_small(),
                fg_color=("#dde3f0", "#1e2a45"), text_color=s.C_TEXT,
                hover_color=s.C_BLUE, corner_radius=8,
                command=lambda d=(id_p, f"{nom} {ape}", id_c, ref): self._pos_sel_persona(d)
            ).pack(fill="x", pady=2, padx=2)

    def _pos_sel_persona(self, data: tuple):
        id_p, nombre, id_c, ref = data
        self.persona_seleccionada = {
            "id_persona": id_p, "nombre": nombre,
            "id_cuenta": id_c,  "cuenta": ref
        }
        self._lbl_persona.configure(text=f"✅  {nombre}  —  {ref}", text_color=s.C_GREEN)
        self._frame_res_persona.grid_forget()
        self._e_persona.delete(0, "end")

    def _pos_finalizar(self):
        if not self.carrito:
            messagebox.showwarning("Carrito vacío", "Agrega productos antes de finalizar.")
            return
        if not self.persona_seleccionada:
            messagebox.showwarning("Sin persona", "Selecciona quién está comprando.")
            return
        metodo   = self._combo_metodo.get()
        total    = round(sum(p["subtotal"] for p in self.carrito), 2)
        total_bs = round(total * self.tasa_bcv, 2)
        try:
            db.registrar_venta(
                self.persona_seleccionada["id_cuenta"],
                self.persona_seleccionada["id_persona"],
                self.carrito, self.tasa_bcv, metodo)
            messagebox.showinfo(
                "✅ Venta Registrada",
                f"Comprador: {self.persona_seleccionada['nombre']}\n"
                f"Cuenta:    {self.persona_seleccionada['cuenta']}\n\n"
                f"Total: ${total:.2f}  /  Bs. {total_bs:,.2f}\nMétodo: {metodo}")
            self.carrito = []
            self._pos_refrescar_carrito()
            self.persona_seleccionada = None
            self._lbl_persona.configure(text="⚠️  Selecciona quién compra", text_color=s.C_ORANGE)
        except Exception as e:
            messagebox.showerror("Error al registrar venta", str(e))

    # ============================================================
    # MÓDULO: CUENTAS Y PERSONAS
    # ============================================================

    def abrir_cuentas(self):
        container = self._mostrar_vista("cuentas")
        
        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=1)
            container.grid_columnconfigure(1, weight=1)
            container.grid_rowconfigure(0, weight=1)
            
            # ── IZQUIERDA: CUENTAS ───────────────────────────────
            fl = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fl.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
            fl.grid_columnconfigure(0, weight=1)

            form = self._card(fl)
            form.pack(fill="x", padx=4, pady=(4, 8))
            form.grid_columnconfigure(0, weight=1)
            form.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(form, text="Cuentas Registradas", font=s.f_subtitulo(), text_color=s.C_TEXT
                         ).grid(row=0, column=0, columnspan=2, pady=(12, 8), padx=14)

            self._e_ref = self._entry(form, ph="Nombre  (Ej: Familia Pérez)")
            self._e_ref.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=4)

            self._e_tel = self._entry(form, ph="Teléfono")
            self._e_tel.grid(row=2, column=0, sticky="ew", padx=12, pady=4)

            self._m_tipo = self._opt(form, s.TIPOS_USUARIO)
            self._m_tipo.grid(row=2, column=1, sticky="ew", padx=12, pady=4)

            self._btn(form, "➕  Crear Cuenta", self._cta_crear, color=s.C_GREEN
                      ).grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(6, 12))

            # ── BARRA DE BÚSQUEDA DINÁMICA DE CUENTAS ──
            self._e_buscar_cta = self._entry(fl, ph="🔍  Buscar cuenta...")
            self._e_buscar_cta.pack(fill="x", padx=4, pady=(0, 6))
            self._e_buscar_cta.bind("<KeyRelease>", self._cta_buscar_evento)

            self._frame_cuentas = ctk.CTkScrollableFrame(fl, fg_color="transparent", corner_radius=0)
            self._frame_cuentas.pack(fill="both", expand=True, padx=4)
            self._frame_cuentas.grid_columnconfigure(0, weight=1)

            # ── DERECHA: PERSONAS ────────────────────────────────
            fr = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            fr.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
            fr.grid_columnconfigure(0, weight=1)

            self._lbl_per_titulo = ctk.CTkLabel(fr, text="👥  Selecciona una cuenta", font=s.f_subtitulo(), text_color=s.C_SUBTEXT)
            self._lbl_per_titulo.pack(pady=(16, 8))

            self._frame_personas = ctk.CTkScrollableFrame(fr, fg_color="transparent", corner_radius=0)
            self._frame_personas.pack(fill="both", expand=True, padx=4)
            self._frame_personas.grid_columnconfigure(0, weight=1)

            self._btn_vincular = self._btn(fr, "➕  Vincular Persona", self._per_abrir_form, color=s.C_BLUE)
            self._btn_vincular.pack(fill="x", padx=14, pady=(6, 4))
            self._btn_vincular.configure(state="disabled")

        self._cta_cargar()

    def _cta_buscar_evento(self, event=None):
        self._cta_cargar(filtro=self._e_buscar_cta.get().strip())

    def _cta_cargar(self, filtro=""):
        for w in self._frame_cuentas.winfo_children():
            w.destroy()
        try:
            filas = db.obtener_cuentas()
            if filtro:
                filas = [f for f in filas if filtro.lower() in f[1].lower()]
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
            
        for f in filas:
            id_c, ref, tel, tipo, deuda, favor = f
            card = self._card(self._frame_cuentas)
            card.pack(fill="x", padx=4, pady=4)
            card.grid_columnconfigure(0, weight=1)

            r0 = ctk.CTkFrame(card, fg_color="transparent")
            r0.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 2))
            r0.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(r0, text=ref, font=s.f_bold(), text_color=s.C_TEXT, anchor="w"
                         ).grid(row=0, column=0, sticky="w")

            tc = {"Estudiante": s.C_BLUE, "Docente": s.C_PURPLE,
                  "Obrero": s.C_ORANGE, "Administrativo": s.C_GREEN}.get(tipo, s.C_BLUE)
            ctk.CTkLabel(r0, text=f" {tipo} ", font=ctk.CTkFont(size=10, weight="bold"),
                         fg_color=tc, corner_radius=6, text_color="white"
                         ).grid(row=0, column=1, padx=(8, 0))

            ctk.CTkLabel(card, text=f"📞 {tel}", font=s.f_small(), text_color=s.C_SUBTEXT, anchor="w"
                         ).grid(row=1, column=0, padx=12, pady=2, sticky="w")

            if float(deuda) > 0:
                stxt, sc = f"⚠️  Deuda: ${float(deuda):.2f}", s.C_ACCENT
            elif float(favor) > 0:
                stxt, sc = f"✅  A favor: ${float(favor):.2f}", s.C_GREEN
            else:
                stxt, sc = "✔️  Sin saldo pendiente", s.C_SUBTEXT

            ctk.CTkLabel(card, text=stxt, font=s.f_bold(), text_color=sc, anchor="w"
                         ).grid(row=2, column=0, padx=12, pady=(2, 4), sticky="w")

            bf = ctk.CTkFrame(card, fg_color="transparent")
            bf.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(2, 10))

            self._btn(bf, "👁  Personas", lambda i=id_c, r=ref: self._cta_seleccionar(i, r), color=s.C_BLUE).pack(side="left", padx=2)
            
            # Botón rápido para realizar abono inmediato
            self._btn(bf, "💰 Abonar", lambda r=ref: self._hist_abono_directo(r), color=s.C_GREEN).pack(side="left", padx=2)
            
            self._btn(bf, "✏️", lambda v=(id_c, ref, tel, tipo): self._cta_editar(v), color="#555").pack(side="left", padx=2)

    def _hist_abono_directo(self, nombre_cuenta: str):
        """Abre la pasarela de abonos rellenando automáticamente el buscador de cuentas."""
        self.abrir_historial()
        self._hist_abono(filtro_inicial=nombre_cuenta)

    def _cta_seleccionar(self, id_cuenta: int, ref: str):
        self._cuenta_sel_id = id_cuenta
        self._lbl_per_titulo.configure(text=f"👥  {ref}", text_color=s.C_TEXT)
        self._btn_vincular.configure(state="normal")
        self._per_cargar(id_cuenta)

    def _cta_crear(self):
        ref  = self._e_ref.get().strip()
        tel  = self._e_tel.get().strip()
        tipo = self._m_tipo.get()
        if not ref or not tel:
            messagebox.showwarning("Atención", "Nombre y teléfono son obligatorios.")
            return
        tiene_hijos = False
        if tipo != "Estudiante":
            tiene_hijos = messagebox.askyesno(
                "¿Tiene hijos en el colegio?",
                f"¿{ref} tiene hijos estudiando aquí?\n\n• Sí → cuenta familiar\n• No → cuenta individual")
        try:
            id_nueva = db.crear_cuenta(ref, tel, tipo)
            if tipo != "Estudiante" and not tiene_hijos:
                partes = ref.strip().split()
                nom = partes[0]
                ape = " ".join(partes[1:]) if len(partes) > 1 else "—"
                db.crear_persona(nom, ape, tipo, None, id_nueva)
            messagebox.showinfo("✅ Cuenta creada", f"Cuenta '{ref}' creada.")
            self._e_ref.delete(0, "end")
            self._e_tel.delete(0, "end")
            self._cta_cargar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cta_editar(self, vals: tuple):
        id_c, ref, tel, tipo = vals
        v = ctk.CTkToplevel(self)
        v.title("Editar Cuenta"); v.geometry("440x300"); v.grab_set()
        ctk.CTkLabel(v, text="Editar Cuenta", font=s.f_subtitulo()).pack(pady=(18, 10))
        e_r = self._entry(v); e_r.insert(0, ref); e_r.pack(pady=6, padx=24, fill="x")
        e_t = self._entry(v); e_t.insert(0, tel); e_t.pack(pady=6, padx=24, fill="x")
        m   = self._opt(v, s.TIPOS_USUARIO); m.set(tipo); m.pack(pady=6, padx=24, fill="x")
        def guardar():
            try:
                db.actualizar_cuenta(id_c, e_r.get().strip(), e_t.get().strip(), m.get())
                messagebox.showinfo("✅", "Cuenta actualizada.")
                self._cta_cargar(); v.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        self._btn(v, "💾  Guardar", guardar, color=s.C_GREEN).pack(pady=14, padx=24, fill="x")

    def _per_cargar(self, id_cuenta: int):
        for w in self._frame_personas.winfo_children():
            w.destroy()
        try:
            filas = db.obtener_personas(id_cuenta)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        if not filas:
            ctk.CTkLabel(self._frame_personas, text="Sin personas vinculadas aún.", font=s.f_normal(), text_color=s.C_SUBTEXT
                         ).pack(pady=20)
            return
        for f in filas:
            id_p, nom, ape, tipo, grado = f
            card = self._card(self._frame_personas)
            card.pack(fill="x", padx=4, pady=5)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=f"{nom} {ape}", font=s.f_bold(), text_color=s.C_TEXT, anchor="w"
                         ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")
            ctk.CTkLabel(card, text=tipo + (f"  ·  {grado}" if grado else ""), font=s.f_small(), text_color=s.C_SUBTEXT, anchor="w"
                         ).grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")
            self._btn(card, "✏️  Editar", lambda d=(id_p, nom, ape, tipo, grado, id_cuenta): self._per_editar(d), color="#555"
                      ).grid(row=0, column=1, rowspan=2, padx=10, pady=6)

    def _per_abrir_form(self):
        if not self._cuenta_sel_id:
            return
        id_c = self._cuenta_sel_id
        v = ctk.CTkToplevel(self)
        v.title("Vincular Persona"); v.geometry("440x380"); v.grab_set()
        ctk.CTkLabel(v, text="Vincular Persona", font=s.f_subtitulo()).pack(pady=(18, 8))
        e_n = self._entry(v, ph="Nombre"); e_n.pack(pady=5, padx=24, fill="x")
        e_a = self._entry(v, ph="Apellido"); e_a.pack(pady=5, padx=24, fill="x")
        e_g = self._entry(v, ph="Grado/Sección (opcional)"); e_g.pack(pady=5, padx=24, fill="x")
        m   = self._opt(v, s.TIPOS_USUARIO); m.pack(pady=5, padx=24, fill="x")
        def guardar():
            if not e_n.get().strip() or not e_a.get().strip():
                messagebox.showwarning("Atención", "Nombre y apellido obligatorios.", parent=v); return
            try:
                db.crear_persona(e_n.get().strip(), e_a.get().strip(), m.get(), e_g.get().strip(), id_c)
                messagebox.showinfo("✅", f"{e_n.get()} vinculado.", parent=v)
                self._per_cargar(id_c); v.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=v)
        self._btn(v, "💾  Guardar", guardar, color=s.C_GREEN).pack(pady=14, padx=24, fill="x")

    def _per_editar(self, datos: tuple):
        id_p, nom, ape, tipo, grado, id_c = datos
        v = ctk.CTkToplevel(self)
        v.title("Editar Persona"); v.geometry("440x380"); v.grab_set()
        ctk.CTkLabel(v, text="Editar Persona", font=s.f_subtitulo()).pack(pady=(18, 8))
        e_n = self._entry(v); e_n.insert(0, nom); e_n.pack(pady=5, padx=24, fill="x")
        e_a = self._entry(v); e_a.insert(0, ape); e_a.pack(pady=5, padx=24, fill="x")
        e_g = self._entry(v, ph="Grado/Sección (opcional)"); e_g.insert(0, grado or ""); e_g.pack(pady=5, padx=24, fill="x")
        m   = self._opt(v, s.TIPOS_USUARIO); m.set(tipo); m.pack(pady=5, padx=24, fill="x")
        def guardar():
            try:
                db.actualizar_persona(id_p, e_n.get().strip(), e_a.get().strip(), m.get(), e_g.get().strip())
                messagebox.showinfo("✅", "Persona actualizada.")
                self._per_cargar(id_c); v.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        self._btn(v, "💾  Guardar", guardar, color=s.C_GREEN).pack(pady=14, padx=24, fill="x")

    # ============================================================
    # MÓDULO: HISTORIAL
    # ============================================================

    def abrir_historial(self):
        container = self._mostrar_vista("historial")
        
        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=1)
            container.grid_rowconfigure(1, weight=1)

            cab = self._card(container)
            cab.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
            cab.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(cab, text="📋  Historial de Pedidos", font=s.f_subtitulo(), text_color=s.C_TEXT
                         ).grid(row=0, column=0, padx=16, pady=14)

            self._e_buscar_hist = self._entry(cab, ph="🔍  Buscar por cuenta o persona...")
            self._e_buscar_hist.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
            self._e_buscar_hist.bind("<KeyRelease>", self._hist_buscar)

            self._btn(cab, "💰  Registrar Abono/Pago", self._hist_abono, color=s.C_BLUE
                      ).grid(row=0, column=2, padx=10, pady=10)

            cuerpo = ctk.CTkFrame(container, corner_radius=0, fg_color=s.C_BG)
            cuerpo.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 12))
            cuerpo.grid_columnconfigure(0, weight=2)
            cuerpo.grid_columnconfigure(1, weight=1)
            cuerpo.grid_rowconfigure(0, weight=1)

            self._frame_trans = ctk.CTkScrollableFrame(cuerpo, fg_color="transparent", corner_radius=0)
            self._frame_trans.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
            self._frame_trans.grid_columnconfigure(0, weight=1)

            self._panel_detalle = self._card(cuerpo)
            self._panel_detalle.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
            self._panel_detalle.grid_columnconfigure(0, weight=1)
            
            self._lbl_placeholder_detalle = ctk.CTkLabel(self._panel_detalle, text="Selecciona un pedido\npara ver el detalle",
                                                         font=s.f_normal(), text_color=s.C_SUBTEXT)
            self._lbl_placeholder_detalle.pack(pady=40)

        self._hist_cargar()

    def _hist_cargar(self, filtro: str = ""):
        for w in self._frame_trans.winfo_children():
            w.destroy()
        try:
            filas = db.obtener_historial(filtro)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        for f in filas:
            id_t, persona, cuenta, fecha, usd, bs, metodo, tipo = f
            es_abono   = tipo == "Abono"
            card_color = ("#eaf7ee", "#0d2b18") if es_abono else s.C_CARD
            card = ctk.CTkFrame(self._frame_trans, corner_radius=12, fg_color=card_color)
            card.pack(fill="x", padx=4, pady=4)
            card.grid_columnconfigure(0, weight=1)

            r0 = ctk.CTkFrame(card, fg_color="transparent")
            r0.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
            r0.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(r0, text=persona, font=s.f_bold(), text_color=s.C_TEXT, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(r0, text="💰 ABONO" if es_abono else "🛒 COMPRA", font=ctk.CTkFont(size=10, weight="bold"),
                         fg_color=s.C_GREEN if es_abono else s.C_BLUE, corner_radius=6, text_color="white"
                         ).grid(row=0, column=1)

            ctk.CTkLabel(card, text=f"📁 {cuenta}  ·  📅 {fmt_fecha(fecha)}", font=s.f_small(), text_color=s.C_SUBTEXT, anchor="w"
                         ).grid(row=1, column=0, padx=12, pady=1, sticky="w")
            ctk.CTkLabel(card, text=f"${float(usd):.2f}  ·  Bs.{float(bs):,.0f}  ·  {metodo}", font=s.f_bold(),
                         text_color=s.C_GREEN if es_abono else s.C_YELLOW, anchor="w"
                         ).grid(row=2, column=0, padx=12, pady=(1, 4), sticky="w")

            bf = ctk.CTkFrame(card, fg_color="transparent")
            bf.grid(row=3, column=0, sticky="ew", padx=10, pady=(2, 10))
            self._btn(bf, "🔍 Detalle", lambda i=id_t: self._hist_detalle(i), color=s.C_BLUE).pack(side="left", padx=4)
            self._btn(bf, "✏️ Editar", lambda d=(id_t, float(usd), metodo): self._hist_editar(d), color="#555").pack(side="left", padx=4)
            self._btn(bf, "🗑️ Eliminar", lambda i=id_t: self._hist_eliminar(i), color=s.C_ACCENT).pack(side="left", padx=4)

    def _hist_buscar(self, event=None):
        self._hist_cargar(self._e_buscar_hist.get().strip())

    def _hist_detalle(self, id_trans: int):
        for w in self._panel_detalle.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._panel_detalle, text="📦  Detalle", font=s.f_bold(), text_color=s.C_TEXT).pack(pady=(14, 8))
        try:
            filas = db.obtener_detalle_transaccion(id_trans)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        if not filas:
            ctk.CTkLabel(self._panel_detalle, text="(Abono — sin productos)", font=s.f_normal(), text_color=s.C_SUBTEXT
                         ).pack(pady=10)
            return
        for f in filas:
            item = self._card(self._panel_detalle)
            item.pack(fill="x", padx=10, pady=3)
            item.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(item, text=f[0], font=s.f_bold(), text_color=s.C_TEXT, anchor="w"
                         ).grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")
            ctk.CTkLabel(item, text=f"x{f[1]}  ·  ${float(f[2]):.2f}  ·  ${float(f[3]):.2f}", font=s.f_small(), text_color=s.C_SUBTEXT, anchor="w"
                         ).grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")

    def _hist_editar(self, datos: tuple):
        id_t, monto, metodo = datos
        v = ctk.CTkToplevel(self)
        v.title("Editar Transacción"); v.geometry("400x260"); v.grab_set()
        ctk.CTkLabel(v, text="Editar Transacción", font=s.f_subtitulo()).pack(pady=(18, 10))
        e_m = self._entry(v, ph="Monto en $"); e_m.insert(0, str(monto)); e_m.pack(pady=6, padx=24, fill="x")
        m_met = self._opt(v, s.METODOS_PAGO); m_met.set(metodo); m_met.pack(pady=6, padx=24, fill="x")
        def guardar():
            try:
                db.actualizar_transaccion(id_t, float(e_m.get()), m_met.get(), self.tasa_bcv)
                messagebox.showinfo("✅", "Transacción actualizada.", parent=v)
                self._hist_cargar(); v.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=v)
        self._btn(v, "💾  Guardar", guardar, color=s.C_GREEN).pack(pady=14, padx=24, fill="x")

    def _hist_eliminar(self, id_trans: int):
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta transacción?\nEsta acción recalculará los saldos y no se puede deshacer."):
            return
        try:
            db.eliminar_transaccion(id_trans)
            messagebox.showinfo("✅", "Transacción eliminada con éxito.")
            self._hist_cargar()
            for w in self._panel_detalle.winfo_children():
                w.destroy()
            ctk.CTkLabel(self._panel_detalle, text="Selecciona un pedido\npara ver el detalle", font=s.f_normal(), text_color=s.C_SUBTEXT).pack(pady=40)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _hist_abono(self, filtro_inicial: str = ""):
        v = ctk.CTkToplevel(self)
        v.title("Registrar Abono / Pago")
        v.geometry("460x440"); v.grab_set()
        ctk.CTkLabel(v, text="💰  Registrar Abono o Pago", font=s.f_subtitulo()).pack(pady=(18, 6))
        
        e_b = self._entry(v, ph="🔍  Buscar cuenta...")
        e_b.pack(pady=6, padx=20, fill="x")

        frame_ctas = ctk.CTkScrollableFrame(v, height=130)
        frame_ctas.pack(fill="x", padx=20, pady=4)
        self._abono_cta = None

        lbl_sel = ctk.CTkLabel(v, text="⚠️  Sin cuenta seleccionada", font=s.f_bold(), text_color=s.C_ORANGE)
        lbl_sel.pack(pady=4)

        def buscar(event=None):
            for w in frame_ctas.winfo_children():
                w.destroy()
            txt = e_b.get().strip()
            if len(txt) < 2:
                return
            try:
                filas = db.buscar_cuentas(txt)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=v); return
            for f in filas:
                id_c, ref, deuda = f
                ctk.CTkButton(
                    frame_ctas, text=f"  {ref}  —  Deuda: ${float(deuda):.2f}",
                    anchor="w", height=36, font=s.f_normal(),
                    fg_color=("#dde3f0", "#1e2a45"), text_color=s.C_TEXT, hover_color=s.C_BLUE,
                    corner_radius=8, command=lambda d=(id_c, ref): sel(d)
                ).pack(fill="x", pady=2)

        def sel(data):
            self._abono_cta = data
            lbl_sel.configure(text=f"✅  {data[1]}", text_color=s.C_GREEN)
            for w in frame_ctas.winfo_children():
                w.destroy()

        e_b.bind("<KeyRelease>", buscar)

        fp = ctk.CTkFrame(v, fg_color="transparent")
        fp.pack(fill="x", padx=20, pady=8)
        fp.grid_columnconfigure(0, weight=1)
        fp.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fp, text="Monto ($):", font=s.f_normal()).grid(row=0, column=0)
        ctk.CTkLabel(fp, text="Método:", font=s.f_normal()).grid(row=0, column=1)

        e_m = self._entry(fp, ph="Ej: 5.00")
        e_m.grid(row=1, column=0, padx=6, sticky="ew")
        m_met = self._opt(fp, ["Efectivo", "Pago Móvil", "Transferencia"])
        m_met.grid(row=1, column=1, padx=6, sticky="ew")

        def confirmar():
            if not self._abono_cta:
                messagebox.showwarning("Atención", "Selecciona una cuenta.", parent=v); return
            try:
                monto = float(e_m.get().strip())
                if monto <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Monto inválido.", parent=v)
                return
            try:
                db.registrar_abono(self._abono_cta[0], monto, self.tasa_bcv, m_met.get())
                messagebox.showinfo(
                    "✅ Abono Registrado",
                    f"Cuenta: {self._abono_cta[1]}\nAbono: ${monto:.2f} / Bs.{monto*self.tasa_bcv:,.0f}\nMétodo: {m_met.get()}", parent=v)
                self._hist_cargar(); v.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=v)

        self._btn(v, "✅  Confirmar Abono", confirmar, color=s.C_GREEN).pack(pady=14, padx=20, fill="x")

        if filtro_inicial:
            e_b.insert(0, filtro_inicial)
            buscar()

    # ============================================================
    # MÓDULO: PRODUCTOS
    # ============================================================

    def abrir_productos(self):
        container = self._mostrar_vista("productos")
        
        if not container.winfo_children():
            container.grid_columnconfigure(0, weight=1)
            container.grid_rowconfigure(1, weight=1)

            top = self._card(container)
            top.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
            top.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(top, text="🍔  Gestión de Productos", font=s.f_subtitulo(), text_color=s.C_TEXT
                         ).grid(row=0, column=0, columnspan=4, pady=(12, 8))

            self._e_nom_p = self._entry(top, ph="Nombre del producto")
            self._e_nom_p.grid(row=1, column=0, sticky="ew", padx=10, pady=8)

            self._m_cat_p = self._opt(top, s.CATEGORIAS)
            self._m_cat_p.grid(row=1, column=1, padx=8, pady=8)

            self._e_precio_p = self._entry(top, ph="Precio $", width=110)
            self._e_precio_p.grid(row=1, column=2, padx=8, pady=8)

            self._btn(top, "🍔  Guardar", self._prod_guardar, color=s.C_GREEN
                      ).grid(row=1, column=3, padx=10, pady=8)

            self._frame_prods = ctk.CTkScrollableFrame(container, fg_color="transparent", corner_radius=0)
            self._frame_prods.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 12))

        self._prod_cargar()

    def _prod_guardar(self):
        nombre = self._e_nom_p.get().strip()
        cat    = self._m_cat_p.get()
        precio = self._e_precio_p.get().strip()
        if not nombre or not precio:
            messagebox.showwarning("Atención", "Nombre y precio son obligatorios.")
            return
        try:
            pval = float(precio)
        except ValueError:
            messagebox.showerror("Error", "Precio inválido."); return
        try:
            db.guardar_producto(nombre, cat, pval)
            messagebox.showinfo("✅", f"'{nombre}' guardado.")
            self._e_nom_p.delete(0, "end")
            self._e_precio_p.delete(0, "end")
            self._prod_cargar()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _prod_cargar(self):
        for w in self._frame_prods.winfo_children():
            w.destroy()
        try:
            categorias = db.obtener_todos_productos()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        for cat, prods in categorias.items():
            color = s.CAT_COLORS.get(cat, s.C_BLUE)
            ctk.CTkLabel(self._frame_prods, text=f"  {cat}", font=s.f_bold(), text_color=color, anchor="w"
                         ).pack(fill="x", padx=6, pady=(14, 4))

            grid = ctk.CTkFrame(self._frame_prods, fg_color="transparent")
            grid.pack(fill="x", padx=4)
            cols = 4

            for i, (id_p, nom, _, precio, estado) in enumerate(prods):
                p    = float(precio)
                disp = estado == "Disponible"
                card = self._card(grid)
                card.grid(row=i // cols, column=i % cols, padx=5, pady=5, sticky="ew")
                card.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(card, text=nom, font=s.f_bold(), text_color=s.C_TEXT if disp else s.C_SUBTEXT, anchor="w"
                             ).grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")
                ctk.CTkLabel(card, text=f"${p:.2f}  ·  Bs.{p * self.tasa_bcv:,.0f}", font=s.f_small(), text_color=color, anchor="w"
                             ).grid(row=1, column=0, padx=10, pady=(0, 4), sticky="w")

                self._btn(card, "✅ Disponible" if disp else "❌ Agotado", lambda i=id_p, d=disp: self._prod_toggle(i, d),
                          color=s.C_ORANGE if disp else "#555", height=s.BTN_HEIGHT_SM
                          ).grid(row=2, column=0, padx=8, pady=(2, 8), sticky="ew")

            for c in range(cols):
                grid.grid_columnconfigure(c, weight=1)

    def _prod_toggle(self, id_prod: int, disponible: bool):
        try:
            db.toggle_estado_producto(id_prod, disponible)
            self._prod_cargar()
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()