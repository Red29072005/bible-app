import flet as ft
import sqlite3
import os
import re
import shutil

class BibliaMotor:
    def __init__(self):
        if os.getenv("ANDROID_DATA"):
            self.base_dir = os.path.join(os.environ["HOME"], "files")
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.path = os.path.join(self.base_dir, "Versiones")
        if not os.path.exists(self.path):
            os.makedirs(self.path, exist_ok=True)

        self.archivos = {
            "NVI": "NVI'22.SQLite3", "LBLA": "LBLA.SQLite3", 
            "DHHS": "DHHS'94.SQLite3", "PDT": "PDT.SQLite3"
        }
        self.archivos_notas = {
            "NVI": "NVI'22.commentaries.SQLite3", "LBLA": "LBLA.commentaries.SQLite3",
            "DHHS": "DHHS'94.commentaries.SQLite3", "PDT": "PDT.commentaries.SQLite3"
        }
        
        self.orden_maestro = [
            "Génesis", "Éxodo", "Levítico", "Números", "Deuteronomio", "Josué", "Jueces", "Job",
            "Rut", "1 Samuel", "2 Samuel", "1 Reyes", "2 Reyes", "Salmo", "Proverbios",
            "Eclesiastés", "Cantares", "1 Crónicas", "2 Crónicas", "Joel", "Amós", "Oseas",
            "Miqueas", "Nahúm", "Jonás", "Habacuc", "Isaías", "Sofonías", "Jeremías",
            "Lamentaciones", "Abdías", "Daniel", "Ezequiel", "Ester", "Hageo", "Zacarías",
            "Malaquías", "Esdras", "Nehemías", "Mateo", "Marcos", "Lucas", "Juan", "Hechos",
            "Romanos", "1 Corintios", "2 Corintios", "Gálatas", "Efesios", "Filipenses",
            "Colosenses", "1 Tesalonicenses", "2 Tesalonicenses", "1 Timoteo", "2 Timoteo",
            "Tito", "Filemón", "Hebreos", "Santiago", "1 Pedro", "2 Pedro", "1 Juan",
            "2 Juan", "3 Juan", "Judas", "Apocalipsis"
        ]
        self.db_user_path = os.path.join(self.path, "user_data.db")
        self._preparar_archivos()
        self.inicializar_db_usuario()

    # OPTIMIZACIÓN DE RAM: Conexiones cortas para dispositivos de 1GB
    def _consultar(self, db_path, query, params=(), fetch=True, commit=False):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            res = cursor.fetchall() if fetch else None
            if commit: conn.commit()
            conn.close()
            return res
        except: return []

    def _preparar_archivos(self):
        bundle_path = os.path.join(os.path.dirname(__file__), "Versiones")
        if os.path.exists(bundle_path) and bundle_path != self.path:
            for f in os.listdir(bundle_path):
                destino = os.path.join(self.path, f)
                if not os.path.exists(destino):
                    shutil.copy2(os.path.join(bundle_path, f), destino)

    def inicializar_db_usuario(self):
        self._consultar(self.db_user_path, "CREATE TABLE IF NOT EXISTS marcadores (libro_id INTEGER, capitulo INTEGER, versiculo INTEGER, color TEXT, PRIMARY KEY (libro_id, capitulo, versiculo))", commit=True)
        self._consultar(self.db_user_path, "CREATE TABLE IF NOT EXISTS ajustes (clave TEXT PRIMARY KEY, valor TEXT)", commit=True)

    def guardar_ajuste(self, clave, valor):
        self._consultar(self.db_user_path, "INSERT OR REPLACE INTO ajustes VALUES (?, ?)", (clave, str(valor)), commit=True)

    def obtener_ajuste(self, clave, por_defecto):
        res = self._consultar(self.db_user_path, "SELECT valor FROM ajustes WHERE clave=?", (clave,))
        return res[0][0] if res else por_defecto

    def guardar_marcador(self, libro_id, cap, vers, color):
        if color is None:
            self._consultar(self.db_user_path, "DELETE FROM marcadores WHERE libro_id=? AND capitulo=? AND versiculo=?", (libro_id, cap, vers), commit=True)
        else:
            self._consultar(self.db_user_path, "INSERT OR REPLACE INTO marcadores VALUES (?, ?, ?, ?)", (libro_id, cap, vers, color), commit=True)

    def obtener_marcadores(self, libro_id, cap):
        res = self._consultar(self.db_user_path, "SELECT versiculo, color FROM marcadores WHERE libro_id=? AND capitulo=?", (libro_id, cap))
        return {row[0]: row[1] for row in res}

    def obtener_id_libro(self, version, nombre):
        ruta = os.path.join(self.path, self.archivos[version])
        res = self._consultar(ruta, "SELECT book_number FROM books WHERE long_name LIKE ? OR short_name LIKE ?", (f"%{nombre}%", f"%{nombre}%"))
        return res[0][0] if res else None

    def obtener_nota(self, version, libro_id, cap, vers):
        if version not in self.archivos_notas: return None
        ruta = os.path.join(self.path, self.archivos_notas[version])
        if not os.path.exists(ruta): return None
        res = self._consultar(ruta, "SELECT text FROM commentaries WHERE book_number=? AND chapter_number_from=? AND verse_number_from=?", (libro_id, cap, vers))
        return res[0][0] if res else None

    def contar_capitulos(self, version, nombre):
        libro_id = self.obtener_id_libro(version, nombre)
        ruta = os.path.join(self.path, self.archivos[version])
        res = self._consultar(ruta, "SELECT MAX(chapter) FROM verses WHERE book_number=?", (libro_id,))
        return int(res[0][0]) if res and res[0][0] else 0

    def obtener_texto(self, version, libro_nombre, cap):
        libro_id = self.obtener_id_libro(version, libro_nombre)
        ruta = os.path.join(self.path, self.archivos[version])
        res = self._consultar(ruta, "SELECT verse, text FROM verses WHERE book_number=? AND chapter=? ORDER BY verse ASC", (libro_id, cap))
        return res, libro_id

def main(page: ft.Page):
    motor = BibliaMotor()
    
    saved_theme = motor.obtener_ajuste("theme", "dark")
    saved_font = int(motor.obtener_ajuste("font_size", 18))
    page.theme_mode = ft.ThemeMode.DARK if saved_theme == "dark" else ft.ThemeMode.LIGHT
    page.horizontal_alignment = "center"
    
    state = {
        "version": "NVI", "libro": "Génesis", "cap": 1, 
        "font_size": saved_font, "libro_id": 1, 
        "v_seleccionados": set(), "textos_cache": {}
    }

    col_lectura = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    txt_label = ft.Text("Génesis 1", size=18, weight="bold")
    txt_preview = ft.Text("Toda la Escritura es inspirada por Dios.\n(2 Timoteo 3:16)", size=state["font_size"])

    # --- BOTTOM SHEETS (SIN ICONOS) ---
    txt_nota_bs = ft.Text("", size=16)
    bs_notas = ft.BottomSheet(
        ft.Container(
            ft.Column([
                ft.Row([
                    ft.Text("Nota de estudio", weight="bold", size=18, color="blue"),
                    ft.TextButton("CERRAR", on_click=lambda _: (setattr(bs_notas, "open", False), page.update())),
                ], alignment="spaceBetween"),
                ft.Divider(),
                ft.Container(txt_nota_bs, padding=ft.Padding(0,0,0,40))
            ], tight=True),
            padding=20, bgcolor="#1A1A1A", border_radius=ft.BorderRadius(20, 20, 0, 0)
        )
    )

    def aplicar_color(color_hex):
        for v in state["v_seleccionados"]:
            motor.guardar_marcador(state["libro_id"], state["cap"], v, color_hex)
        state["v_seleccionados"].clear()
        bs_colores.open = False
        cargar_capitulo()
        page.update()

    def copiar_versiculos(e):
        if not state["v_seleccionados"]: return
        lista_ordenada = sorted(list(state["v_seleccionados"]))
        texto_final = f"{state['libro']} {state['cap']}\n"
        for v in lista_ordenada:
            texto_final += f"{v}. {state['textos_cache'].get(v, '')}\n"
        page.set_clipboard(texto_final)
        state["v_seleccionados"].clear()
        bs_colores.open = False
        cargar_capitulo()
        page.snack_bar = ft.SnackBar(ft.Text("Copiado al portapapeles"))
        page.snack_bar.open = True
        page.update()

    def crear_bolita(color_hex):
        return ft.Container(
            width=45, height=45, bgcolor=color_hex, shape=ft.BoxShape.CIRCLE,
            on_click=lambda _: aplicar_color(color_hex),
            border=ft.Border.all(1, "white24")
        )

    bs_colores = ft.BottomSheet(
        ft.Container(
            ft.Column([
                ft.Text("OPCIONES", weight="bold", size=18),
                ft.Row([
                    crear_bolita("#99FFFF00"), crear_bolita("#99AAFF00"), 
                    crear_bolita("#9900CCFF"), crear_bolita("#99CC99FF"), 
                    crear_bolita("#99FF99CC"),
                ], alignment="center", spacing=15),
                ft.Row([
                    ft.TextButton("COPIAR", on_click=copiar_versiculos),
                    ft.TextButton("LIMPIAR", on_click=lambda _: aplicar_color(None)),
                ], alignment="center"),
                ft.TextButton("CANCELAR", on_click=lambda _: (setattr(bs_colores, "open", False), page.update()))
            ], tight=True, horizontal_alignment="center"),
            padding=25, bgcolor="#1A1A1A", border_radius=ft.BorderRadius(20, 20, 0, 0)
        )
    )
    page.overlay.extend([bs_notas, bs_colores])

    def abrir_nota(texto):
        t = re.sub(r'<[^>]+>', '', str(texto))
        t = re.sub(r'\[\d+\]', '', t).strip() 
        txt_nota_bs.value = t
        bs_notas.open = True
        page.update()

    def gestionar_seleccion(v_num):
        if v_num in state["v_seleccionados"]:
            state["v_seleccionados"].remove(v_num)
        else:
            state["v_seleccionados"].add(v_num)
        cargar_capitulo()
        page.update()

    def abrir_menu_marcar(v_num):
        if not state["v_seleccionados"]: state["v_seleccionados"].add(v_num)
        bs_colores.open = True
        page.update()

    def cargar_capitulo():
        datos, libro_id = motor.obtener_texto(state["version"], state["libro"], state["cap"])
        state["libro_id"] = libro_id
        marcadores = motor.obtener_marcadores(libro_id, state["cap"])
        state["textos_cache"].clear()
        col_lectura.controls.clear()
        
        for v_num, v_txt in datos:
            limpio = re.sub(r'<[^>]+>|\[\d+\]|[\u2460-\u24FF]', '', str(v_txt))
            limpio = re.sub(r'\s+', ' ', limpio).replace(" ,", ",").replace(" .", ".").strip()
            state["textos_cache"][v_num] = limpio
            
            bg_color = marcadores.get(v_num, None)
            nota_txt = motor.obtener_nota(state["version"], libro_id, state["cap"], v_num)
            esta_sel = v_num in state["v_seleccionados"]
            
            spans = [
                ft.TextSpan(f" {v_num} ", style=ft.TextStyle(color="grey", size=max(10, state["font_size"]-4))),
                ft.TextSpan(limpio, style=ft.TextStyle(size=state["font_size"], bgcolor=bg_color, weight="bold" if esta_sel else None, italic=esta_sel))
            ]
            
            if nota_txt:
                spans.append(ft.TextSpan(" [#]", on_click=lambda e, nt=nota_txt: abrir_nota(nt), 
                                       style=ft.TextStyle(color="blue", weight="bold", size=state["font_size"]+2)))

            col_lectura.controls.append(
                ft.GestureDetector(
                    content=ft.Container(content=ft.Text(spans=spans), padding=2),
                    on_tap=lambda e, vn=v_num: gestionar_seleccion(vn),
                    on_long_press=lambda e, vn=v_num: abrir_menu_marcar(vn)
                )
            )
        txt_label.value = f"{state['libro']} {state['cap']}"
        view_inicio.visible = view_libros.visible = view_caps.visible = view_ajustes.visible = False
        view_lectura.visible = True
        page.update()

    # --- AJUSTES EVENTOS ---
    def cambiar_tema(e):
        page.theme_mode = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
        motor.guardar_ajuste("theme", "dark" if e.control.value else "light")
        page.update()

    def cambiar_fuente(e):
        state["font_size"] = int(float(e.control.value))
        txt_preview.size = state["font_size"]
        motor.guardar_ajuste("font_size", state["font_size"])
        page.update()

    # --- VISTAS (MANTENIENDO TU DISEÑO) ---
    view_ajustes = ft.Column([
        ft.Text("CONFIGURACIÓN", size=24, weight="bold"),
        ft.Divider(),
        ft.Switch(label="Modo Oscuro", value=(page.theme_mode == ft.ThemeMode.DARK), on_change=cambiar_tema),
        ft.Text("Tamaño de letra:"),
        ft.Slider(min=14, max=40, value=state["font_size"], on_change=cambiar_fuente),
        ft.Container(txt_preview, padding=20, border=ft.Border.all(1, "grey"), border_radius=10),
        ft.TextButton("VOLVER", on_click=lambda _: (setattr(view_inicio, 'visible', True), setattr(view_ajustes, 'visible', False), page.update()))
    ], visible=False, horizontal_alignment="center")

    grid_libros = ft.Column(scroll=ft.ScrollMode.AUTO)
    def mostrar_selector_libros():
        grid_libros.controls = [ft.TextButton(content=ft.Text(l, size=22, weight="w500"), on_click=lambda e, lib=l: mostrar_selector_caps(lib)) for l in motor.orden_maestro]
        view_lectura.visible, view_libros.visible = False, True
        page.update()

    grid_caps = ft.Row(wrap=True, scroll=ft.ScrollMode.AUTO, alignment="center")
    def mostrar_selector_caps(libro_nombre):
        state["libro"] = libro_nombre
        n = motor.contar_capitulos(state["version"], libro_nombre)
        grid_caps.controls = [ft.TextButton(content=ft.Text(str(i), size=18), on_click=lambda e, x=i: (state.update({"cap": x}), cargar_capitulo())) for i in range(1, n + 1)]
        view_libros.visible, view_caps.visible = False, True
        page.update()

    view_libros = ft.Column([ft.TextButton("VOLVER", on_click=lambda _: (setattr(view_libros, 'visible', False), setattr(view_lectura, 'visible', True), page.update())), ft.Container(content=grid_libros, expand=True)], visible=False, expand=True)
    view_caps = ft.Column([ft.TextButton("VOLVER", on_click=lambda _: mostrar_selector_libros()), ft.Container(content=grid_caps, expand=True)], visible=False, expand=True)

    view_lectura = ft.Column([
        ft.Container(padding=10, content=ft.Row([
            ft.TextButton(content=txt_label, on_click=lambda _: mostrar_selector_libros()),
            ft.TextButton("MENU", on_click=lambda _: (setattr(view_inicio, 'visible', True), setattr(view_lectura, 'visible', False), page.update())),
        ], alignment="spaceBetween")),
        ft.Container(content=col_lectura, expand=True, padding=15),
        ft.Row([
            ft.TextButton("<< ANT", on_click=lambda _: (state.update({"cap": max(1, state["cap"]-1)}), cargar_capitulo())),
            ft.TextButton("SIG >>", on_click=lambda _: (state.update({"cap": state["cap"]+1}), cargar_capitulo())),
        ], alignment="center")
    ], visible=False, expand=True)

    dd_version = ft.Dropdown(label="Versión", width=250, value="NVI", options=[ft.dropdown.Option(k) for k in motor.archivos.keys()])
    view_inicio = ft.Column([
        ft.Text("BIBLIA", size=30, weight="bold"),
        ft.Container(height=20),
        dd_version,
        ft.Container(height=20),
        ft.FilledButton("LEER AHORA", width=220, height=50, on_click=lambda _: (state.update({"version": dd_version.value}), cargar_capitulo())),
        ft.Container(height=10),
        ft.TextButton("AJUSTES", on_click=lambda _: (setattr(view_inicio, 'visible', False), setattr(view_ajustes, 'visible', True), page.update()))
    ], horizontal_alignment="center", alignment="center", expand=True)

    page.add(ft.Container(content=ft.Stack([view_inicio, view_lectura, view_libros, view_caps, view_ajustes]), expand=True))

if __name__ == "__main__":
    ft.run(main)