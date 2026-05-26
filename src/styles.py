"""
styles.py
=========
Configuración visual del Sistema de Gestión - Cantina R.R.
Todos los colores, fuentes y helpers de estilo viven aquí.
Para cambiar la apariencia del sistema, solo modifica este archivo.
"""

import customtkinter as ctk

# ── TEMA GENERAL ─────────────────────────────────────────────
MODO      = "dark"   # "dark" o "light"
TEMA_CTK  = "blue"   # "blue", "green", "dark-blue"

# ── COLORES PRINCIPALES ──────────────────────────────────────
# Cada color es una tupla (modo_claro, modo_oscuro)
# o un string hex único para ambos modos.

C_BG      = ("#f0f0f0", "#1a1a2e")   # Fondo general
C_CARD    = ("#ffffff", "#16213e")   # Tarjetas / paneles
C_NAV     = ("#1a1a2e", "#0f0f1a")   # Barra lateral

# Colores de acción
C_GREEN   = "#00b894"   # Confirmaciones, éxito, saldo a favor
C_BLUE    = "#0984e3"   # Acciones principales, navegación
C_ORANGE  = "#e17055"   # Advertencias, botón "−", Por Unidad
C_YELLOW  = "#fdcb6e"   # Totales en Bs.
C_PURPLE  = "#6c5ce7"   # Combos
C_ACCENT  = "#e94560"   # Eliminar, deuda, alertas

# Colores de texto
C_TEXT    = ("#1a1a2e", "#ffffff")   # Texto principal
C_SUBTEXT = ("#636e72", "#b2bec3")   # Texto secundario

# ── COLORES POR CATEGORÍA DE PRODUCTO ───────────────────────
CAT_COLORS = {
    "Por Unidad": C_ORANGE,
    "Combos":     C_PURPLE,
    "Bebidas":    C_BLUE,
    "Meriendas":  C_GREEN,
}

# ── LISTAS DE OPCIONES (constantes de dominio) ───────────────
CATEGORIAS    = ["Por Unidad", "Combos", "Bebidas", "Meriendas"]
METODOS_PAGO  = ["Efectivo", "Pago Móvil", "Transferencia", "Pendiente"]
TIPOS_USUARIO = ["Estudiante", "Docente", "Obrero", "Administrativo"]

# ── TAMAÑOS ──────────────────────────────────────────────────
BTN_HEIGHT    = 42   # Altura estándar de botones
BTN_HEIGHT_SM = 30   # Botones pequeños (+ / -)
BTN_HEIGHT_LG = 52   # Botones destacados (Finalizar venta)
CORNER        = 10   # Radio de esquinas estándar
CORNER_CARD   = 14   # Radio de esquinas de tarjetas


# ── FUNCIONES DE UTILIDAD ────────────────────────────────────

def hover(hex_color: str) -> str:
    """Oscurece un color hex para usarlo como hover."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
        return f"#{max(0, r-30):02x}{max(0, g-30):02x}{max(0, b-30):02x}"
    except Exception:
        return hex_color


def aplicar_tema():
    """Aplica el tema global de CustomTkinter."""
    ctk.set_appearance_mode(MODO)
    ctk.set_default_color_theme(TEMA_CTK)


# ── FUENTES ──────────────────────────────────────────────────
# Se usan como funciones porque CTkFont debe crearse
# después de inicializar la ventana.

def f_titulo():    return ctk.CTkFont(size=20, weight="bold")
def f_subtitulo(): return ctk.CTkFont(size=16, weight="bold")
def f_normal():    return ctk.CTkFont(size=13)
def f_bold():      return ctk.CTkFont(size=13, weight="bold")
def f_small():     return ctk.CTkFont(size=11)
def f_total():     return ctk.CTkFont(size=26, weight="bold")
def f_nav():       return ctk.CTkFont(size=13, weight="bold")