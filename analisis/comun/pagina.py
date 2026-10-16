"""
Escribe la página web de una investigación con la misma cabecera, menú y pie
que el resto de proyectos de Línea de pase.

La cabecera y el pie se copian de proyectos/futbol-femenino/index.html, así
que si cambian allí (por ejemplo, la versión de estilo.css) las páginas nuevas
los recogen la próxima vez que se generen.
"""
import re
from pathlib import Path

RAIZ_WEB = Path(__file__).resolve().parents[2]
PLANTILLA = RAIZ_WEB / "proyectos" / "futbol-femenino" / "index.html"


def escribir_pagina(carpeta, titulo, descripcion, migas, cuerpo, fuentes_pie):
    """
    carpeta:     carpeta de la página dentro de proyectos/ (por ejemplo «liga-f-xt»)
    titulo:      título de la pestaña del navegador
    descripcion: resumen para buscadores y para la vista previa al compartir
    migas:       texto tras «Proyectos /» (por ejemplo «Investigación»)
    cuerpo:      HTML del contenido, desde la cabecera del proyecto hasta el final
    fuentes_pie: primera línea del pie con las fuentes
    """
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    cabeza = plantilla.split("</head>", 1)[0]
    cabeza = re.sub(r"<title>.*?</title>", f"<title>{titulo} · Línea de pase</title>", cabeza)
    cabeza = re.sub(r'<meta name="description" content=".*?">',
                    f'<meta name="description" content="{descripcion}">', cabeza)
    # Vista previa al compartir el enlace en redes.
    cabeza += (f'<meta property="og:title" content="{titulo}">\n'
               f'<meta property="og:description" content="{descripcion}">\n'
               f'<meta property="og:image" content="https://lineadepase.github.io/proyectos/{carpeta}/graficos/compartir.png">\n'
               '<link rel="stylesheet" href="../../assets/investigacion.css?v=20261016">\n')
    menu = re.search(r'<header class="cabecera">.*?</header>', plantilla, re.S).group(0)
    pie = re.search(r'<footer class="pie">.*?</footer>', plantilla, re.S).group(0)
    pie = re.sub(r"<p>Fuentes:.*?</p>", f"<p>{fuentes_pie}</p>", pie, count=1, flags=re.S)

    pagina = (f"{cabeza}</head>\n<body>\n{menu}\n\n<main class=\"envoltorio\">\n"
              f"  <p class=\"migas\"><a href=\"../index.html\">Proyectos</a> / {migas}</p>\n"
              f"{cuerpo}\n</main>\n\n{pie}\n</body>\n</html>\n")
    destino = RAIZ_WEB / "proyectos" / carpeta / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    return destino


def numero(valor, decimales=3):
    """Número con coma decimal y punto de miles, como se escribe en español."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", " ").replace(".", ",").replace(" ", ".")


def escribir_pagina_zaragoza(archivo, titulo, descripcion, migas, cuerpo, fuentes_pie):
    """
    Página dentro de la sección del Real Zaragoza (tema azul y blanco, con sus
    pestañas). Copia cabecera, pestañas y pie de proyectos/real-zaragoza/grupo-2.html,
    que es la pestaña de la que cuelga.
    """
    plantilla = (RAIZ_WEB / "proyectos" / "real-zaragoza" / "grupo-2.html").read_text(encoding="utf-8")
    cabeza = plantilla.split("</head>", 1)[0]
    cabeza = re.sub(r"<title>.*?</title>", f"<title>{titulo} · Línea de pase</title>", cabeza)
    cabeza = re.sub(r'<meta name="description" content=".*?">',
                    f'<meta name="description" content="{descripcion}">', cabeza)
    cabeza += (f'<meta property="og:title" content="{titulo}">\n'
               f'<meta property="og:description" content="{descripcion}">\n'
               f'<meta property="og:image" content="https://lineadepase.github.io/proyectos/real-zaragoza/graficos/simulacion/compartir.png">\n'
               '<link rel="stylesheet" href="../../assets/investigacion.css?v=20261016">\n')
    menu = re.search(r'<header class="cabecera">.*?</header>', plantilla, re.S).group(0)
    pestanas = re.search(r'<nav class="pestanas".*?</nav>', plantilla, re.S).group(0)
    pie = re.search(r'<footer class="pie">.*?</footer>', plantilla, re.S).group(0)
    pie = re.sub(r"<p>Fuentes?:.*?</p>", f"<p>{fuentes_pie}</p>", pie, count=1, flags=re.S)
    pagina = (f"{cabeza}</head>\n<body>\n{menu}\n\n<main class=\"envoltorio\">\n"
              f"  <p class=\"migas\"><a href=\"../index.html\">Proyectos</a> / <a href=\"index.html\">Real Zaragoza 2026/27</a> / {migas}</p>\n"
              f"  {pestanas}\n{cuerpo}\n</main>\n\n{pie}\n</body>\n</html>\n")
    destino = RAIZ_WEB / "proyectos" / "real-zaragoza" / archivo
    destino.write_text(pagina, encoding="utf-8")
    return destino


def figura_foto(src, meta):
    """
    Foto de cabecera de una investigación con su crédito completo: autor,
    licencia enlazada, procedencia y cambios hechos, como piden las licencias
    Creative Commons.
    """
    return (f'  <figure class="figura foto-cabecera"><img src="{src}" alt="{meta["descripcion"]}" loading="lazy">'
            f'<figcaption>{meta["descripcion"]}. Foto: {meta["autor"]}, '
            f'<a href="{meta["licencia_url"]}">{meta["licencia"]}</a>, '
            f'<a href="{meta["pagina"]}">Wikimedia Commons</a> ({meta["cambios"]}).</figcaption></figure>')


def credito_corto(meta):
    """Crédito breve para escribir sobre la foto en las imágenes de redes."""
    licencia = "CC0" if meta["licencia"].startswith("CC0") else meta["licencia"]
    return f'Foto: {meta["autor"]} ({meta["lugar_fecha"]}) · {licencia} · Wikimedia Commons'
