"""
styles.py
=========
Configuración visual · Sistema de Gestión · Cantina R.R.
Estética: Claymorfismo Verde & Blanco
──────────────────────────────────────────────────────────
Filosofía de diseño
  • Luz primaria: verde fresco + blanco cálido como alma del sistema.
  • Dark secundario: verdes profundos (sin azules).
  • Claymorfismo: esquinas muy redondeadas, sombras soft apiladas,
    elementos "gordos" con padding generoso → UI amigable y acogedora.
  • Tipografía moderna por plataforma, escala generosa.

Para cambiar la apariencia del sistema, solo modifica este archivo.
"""

import platform
import customtkinter as ctk

# ╔══════════════════════════════════════════════════════════════╗
# ║  TEMA GLOBAL                                                 ║
# ╚══════════════════════════════════════════════════════════════╝
MODO = "light"  # ← luz como estado natural; dark como alternativa
TEMA_CTK = "green"  # tema base de CTk (blue / green / dark-blue)


# ╔══════════════════════════════════════════════════════════════╗
# ║  PALETA · CLAYMORFISMO VERDE & BLANCO                        ║
# ╚══════════════════════════════════════════════════════════════╝
#   Cada constante es una tupla ("light", "dark") que CTk entiende
#   nativamente. Los colores únicos (sin dark companion) son
#   constantes planas usadas igual en ambos modos.

# ── Fondos ──────────────────────────────────────────────────────
C_BG = ("#e6e9e8", "#0b1a14")  # Menta muy suave / verde noche
C_BG2 = ("#d1d6d4", "#0e2019")  # Segundo nivel (bajo tarjetas)
C_BG3 = ("#d0e8dc", "#112418")  # Tercer nivel (secciones sumidas)

# ── Tarjetas ─────────────────────────────────────────────────────
C_CARD = ("#ffffff", "#122a1f")  # Blanco puro / verde oscuro profundo
C_CARD_UP = ("#f5fdf8", "#1a3829")  # Tarjeta elevada (hover / activa)

# ── Sombra clay (frame apilado detrás de tarjetas) ───────────────
C_SHADOW = ("#c4dfd1", "#071510")  # Color del "relieve" clay

# ── Bordes ───────────────────────────────────────────────────────
C_BORDER = ("#a0c8b2", "#2a5a40")  # Borde visible — era demasiado suave
C_BORDER_FOCUS = ("#2e8b5a", "#4db87a")  # Borde activo / foco

# ── Barra lateral ────────────────────────────────────────────────
C_NAV = ("#082e1d", "#05140d")  # Verde bosque oscuro
C_NAV_ITEM = ("#1a5c3e", "#1a4030")  # Ítem hover / activo
C_NAV_SELECTED = ("#ffffff1a", "#ffffff14")  # Seleccionado translúcido
C_NAV_TEXT = ("#ffffff", "#e8f5ee")  # Texto en sidebar

# ── Acción principal ─────────────────────────────────────────────
C_PRIMARY = "#2e8b5a"  # Verde bosque — botón primario
C_PRIMARY_H = "#236b44"  # Hover primario

C_SECONDARY = "#57a87a"  # Verde claro — botón secundario
C_SECONDARY_H = "#4a9169"

# ── Semáforo de estado ───────────────────────────────────────────
C_SUCCESS = "#27ae60"  # Verde oscuro — confirmación
C_WARNING = "#e8a020"  # Ámbar cálido — advertencia
C_DANGER = "#e05252"  # Rojo coral suave — eliminar / deuda
C_INFO = "#3a9fbf"  # Azul agua — información neutra

# ── Especiales / Categorías ──────────────────────────────────────
C_YELLOW = "#f0c030"  # Totales / destacado
C_PURPLE = "#9b6ec8"  # Combos
C_ORANGE = "#e07830"  # Por Unidad
C_TEAL = "#26a69a"  # Bebidas (agua fresca)

# ── Aliases de compatibilidad (código existente) ─────────────────
#    El código antiguo usaba C_GREEN, C_BLUE, C_ACCENT.
#    Mapeamos a los nuevos nombres para evitar romper nada.
C_GREEN = C_SUCCESS  # ← era "#2ecc71", ahora "#27ae60" (verde oscuro)
C_BLUE = C_TEAL  # ← era "#3498db", ahora "#26a69a" (teal/agua)
C_ACCENT = C_DANGER  # ← era "#e74c3c", ahora "#e05252" (rojo coral)

# ── Texto ────────────────────────────────────────────────────────
C_TEXT = ("#051a10", "#e8f5ee")  # Principal — verde muy oscuro / blanco menta
C_SUBTEXT = ("#4a665a", "#8ab8a0")  # Secundario — verde apagado
C_MUTED = ("#90b0a0", "#3a6050")  # Desactivado / placeholder


# ╔══════════════════════════════════════════════════════════════╗
# ║  CATEGORÍAS DE PRODUCTO                                      ║
# ╚══════════════════════════════════════════════════════════════╝
CAT_COLORS = {
    "Por Unidad": C_ORANGE,
    "Combos": C_PURPLE,
    "Bebidas": C_TEAL,
    "Meriendas": C_PRIMARY,
}

# ── Listas de dominio ────────────────────────────────────────────
CATEGORIAS = ["Por Unidad", "Combos", "Bebidas", "Meriendas"]
METODOS_PAGO = ["Efectivo", "Pago Móvil", "Transferencia", "Pendiente"]
TIPOS_USUARIO = ["Estudiante", "Docente", "Obrero", "Administrativo"]
NIVELES_ESTUDIANTE = ["Preescolar", "Básica", "Bachillerato"]


# ╔══════════════════════════════════════════════════════════════╗
# ║  DIMENSIONES · FILOSOFÍA CLAY                                ║
# ╚══════════════════════════════════════════════════════════════╝
#   El claymorfismo usa elementos "gordos" con esquinas muy
#   redondeadas y espacio interno generoso → sensación táctil/amable.

BTN_HEIGHT = 46  # Botón estándar (más alto que convencional)
BTN_HEIGHT_SM = 34  # Botón pequeño (contador +/−)
BTN_HEIGHT_LG = 58  # Botón primario destacado (Finalizar venta)

CORNER = 16  # Esquina estándar (inputs, dropdowns)
CORNER_CARD = 22  # Tarjetas muy redondeadas ← firma clay
CORNER_BTN = 14  # Botones
CORNER_BTN_SM = 10  # Botones pequeños
CORNER_NAV = 12  # Ítem de navegación
CORNER_BADGE = 20  # Badges / etiquetas (cápsula completa)

PADDING = 20  # Padding interno de tarjetas
PADDING_LG = 28  # Secciones principales
PADDING_SM = 12  # Elementos compactos

SHADOW_OFFSET = 4  # Píxeles de desplazamiento del frame-sombra clay
BORDER_WIDTH = 2  # Ancho de borde estándar

# ── Ancho del sidebar ────────────────────────────────────────────
NAV_WIDTH = 220


# ╔══════════════════════════════════════════════════════════════╗
# ║  TIPOGRAFÍA                                                  ║
# ╚══════════════════════════════════════════════════════════════╝
#   Detección de la mejor fuente disponible por plataforma.
#   El claymorfismo combina mejor con fuentes redondeadas / amables.
#   Si la fuente elegida no existe en el sistema, CTk usa el
#   default del SO (nunca falla).


def _detectar_fuente() -> str:
    sistema = platform.system()
    if sistema == "Windows":
        # Segoe UI Variable es más redondeada y moderna (Windows 11)
        # Segoe UI como fallback seguro (Windows 10)
        return "Segoe UI Variable"
    elif sistema == "Darwin":
        # SF Pro Rounded es ideal para claymorfismo en macOS
        return "SF Pro Rounded"
    else:
        # Ubuntu tiene terminaciones redondeadas, muy disponible en Linux
        return "Ubuntu"


FONT = _detectar_fuente()

#   Escala tipográfica: generosa y jerarquizada
#   (Cada función crea un nuevo objeto CTkFont; deben llamarse
#   después de inicializar la ventana CTk)


def f_display():
    return ctk.CTkFont(family=FONT, size=34, weight="bold")


def f_titulo():
    return ctk.CTkFont(family=FONT, size=26, weight="bold")


def f_subtitulo():
    return ctk.CTkFont(family=FONT, size=20, weight="bold")


def f_seccion():
    return ctk.CTkFont(family=FONT, size=17, weight="bold")


def f_normal():
    return ctk.CTkFont(family=FONT, size=16)


def f_bold():
    return ctk.CTkFont(family=FONT, size=16, weight="bold")


def f_small():
    return ctk.CTkFont(family=FONT, size=13)


def f_small_bold():
    return ctk.CTkFont(family=FONT, size=13, weight="bold")


def f_total():
    return ctk.CTkFont(family=FONT, size=34, weight="bold")


def f_nav():
    return ctk.CTkFont(family=FONT, size=14, weight="bold")


def f_badge():
    return ctk.CTkFont(family=FONT, size=12, weight="bold")


def f_input():
    return ctk.CTkFont(family=FONT, size=15)


# ╔══════════════════════════════════════════════════════════════╗
# ║  PRESETS DE WIDGET                                           ║
# ╚══════════════════════════════════════════════════════════════╝
#   Diccionarios listos para desempacar (**) en widgets CTk.
#   Uso: ctk.CTkButton(parent, **BTN_PRIMARY, text="Guardar")

CARD_STYLE = dict(
    corner_radius=CORNER_CARD,
    fg_color=C_CARD,
    border_width=BORDER_WIDTH,
    border_color=C_BORDER,
)

# Botón primario (acción principal)
BTN_PRIMARY = dict(
    height=BTN_HEIGHT,
    corner_radius=CORNER_BTN,
    fg_color=C_PRIMARY,
    hover_color=C_PRIMARY_H,
    text_color="#ffffff",
)

# Botón primario grande (ej. "Finalizar Venta")
BTN_PRIMARY_LG = dict(
    height=BTN_HEIGHT_LG,
    corner_radius=CORNER_BTN,
    fg_color=C_PRIMARY,
    hover_color=C_PRIMARY_H,
    text_color="#ffffff",
)

# Botón secundario / outlinado
BTN_SECONDARY = dict(
    height=BTN_HEIGHT,
    corner_radius=CORNER_BTN,
    fg_color=C_CARD,
    hover_color=C_BG2,
    text_color=C_TEXT,
    border_width=BORDER_WIDTH,
    border_color=C_BORDER,
)

# Botón de peligro (eliminar, cancelar)
BTN_DANGER = dict(
    height=BTN_HEIGHT,
    corner_radius=CORNER_BTN,
    fg_color=C_DANGER,
    hover_color="#c44040",
    text_color="#ffffff",
)

# Botón fantasma (texto solo, sin fondo)
BTN_GHOST = dict(
    height=BTN_HEIGHT,
    corner_radius=CORNER_BTN,
    fg_color="transparent",
    hover_color=C_BG2,
    text_color=C_PRIMARY,
    border_width=0,
)

# Botón pequeño (contadores +/−)
BTN_SMALL = dict(
    height=BTN_HEIGHT_SM,
    width=BTN_HEIGHT_SM,
    corner_radius=CORNER_BTN_SM,
    fg_color=C_BG2,
    hover_color=C_BG3,
    text_color=C_TEXT,
)

# Input / Entry estándar
INPUT_STYLE = dict(
    corner_radius=CORNER,
    border_width=BORDER_WIDTH,
    border_color=C_BORDER,
    fg_color=C_CARD,
    text_color=C_TEXT,
)

# Dropdown / OptionMenu
DROPDOWN_STYLE = dict(
    corner_radius=CORNER,
    fg_color=C_CARD,
    button_color=C_SECONDARY,
    button_hover_color=C_SECONDARY_H,
    dropdown_fg_color=C_CARD,
    text_color=C_TEXT,
)


# ╔══════════════════════════════════════════════════════════════╗
# ║  HELPER · SOMBRA CLAY                                        ║
# ╚══════════════════════════════════════════════════════════════╝
def crear_card_clay(parent, **kwargs) -> tuple:
    """
    Crea una tarjeta con efecto clay apilado:
      [frame sombra] → [frame tarjeta encima, desplazado -offset]

    Retorna (frame_sombra, frame_tarjeta).
    El contenido va dentro de frame_tarjeta.

    Uso:
        sombra, card = crear_card_clay(parent)
        sombra.pack(padx=20, pady=20)
        ctk.CTkLabel(card, text="Hola").pack(padx=16, pady=16)
    """
    offset = kwargs.pop("shadow_offset", SHADOW_OFFSET)
    radius = kwargs.pop("corner_radius", CORNER_CARD)

    # Frame sombra (fondo ligeramente más oscuro/verde)
    frame_sombra = ctk.CTkFrame(
        parent,
        corner_radius=radius,
        fg_color=C_SHADOW,
        **kwargs,
    )

    # Frame tarjeta (encima, desplazado hacia arriba-izquierda)
    frame_card = ctk.CTkFrame(
        frame_sombra,
        corner_radius=radius,
        fg_color=C_CARD,
        border_width=BORDER_WIDTH,
        border_color=C_BORDER,
    )
    frame_card.place(relx=0, rely=0, relwidth=1, relheight=1, x=-offset, y=-offset)

    return frame_sombra, frame_card


# ╔══════════════════════════════════════════════════════════════╗
# ║  FUNCIONES DE UTILIDAD                                       ║
# ╚══════════════════════════════════════════════════════════════╝


def hover(hex_color: str, amount: int = 28) -> str:
    """Oscurece un color hex para usarlo como estado hover."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        return f"#{max(0, r-amount):02x}{max(0, g-amount):02x}{max(0, b-amount):02x}"
    except Exception:
        return hex_color


def lighten(hex_color: str, amount: int = 28) -> str:
    """Aclara un color hex (útil para estados desactivados)."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
        return (
            f"#{min(255, r+amount):02x}{min(255, g+amount):02x}{min(255, b+amount):02x}"
        )
    except Exception:
        return hex_color


def hex_a_rgba(hex_color: str, alpha: float) -> str:
    """Convierte hex + alpha a string rgba para uso en Canvas/PIL."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def color_categoria(categoria: str) -> str:
    """Devuelve el color asociado a una categoría de producto."""
    return CAT_COLORS.get(categoria, C_PRIMARY)


def aplicar_tema():
    """Aplica el tema global de CustomTkinter (llamar antes de crear widgets)."""
    ctk.set_appearance_mode(MODO)
    ctk.set_default_color_theme(TEMA_CTK)


def toggle_modo() -> str:
    """
    Alterna entre modo claro y oscuro en tiempo real.
    Retorna el modo resultante ("light" / "dark").
    """
    global MODO
    MODO = "dark" if MODO == "light" else "light"
    ctk.set_appearance_mode(MODO)
    return MODO
