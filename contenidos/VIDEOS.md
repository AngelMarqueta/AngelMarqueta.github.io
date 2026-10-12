# Identidad para futuros vídeos

Marca: **Línea de pase**. Nombre público y firma del autor: **Ángel Marqueta Alonso**.

Usar este nombre en títulos de autor, guiones, locución, tarjetas de cierre, subtítulos, miniaturas, créditos y metadatos. Los datos comunes están en `identidad.json`.

El cierre incluye la web https://lineadepase.github.io/ y el perfil de LinkedIn. Mantener los créditos de las fuentes, música y sus licencias.

Preparar versión horizontal para la web y LinkedIn, y vertical para reels. Comprobar el cierre completo antes de publicar.

## Tarjeta de cierre reutilizable

`generar_cierre.py` toma el nombre y los enlaces de `identidad.json`. Requiere Pillow y qrcode.

```sh
python contenidos/generar_cierre.py --output cierre.png
```

Se pueden indicar fuentes instaladas con `--font` y `--font-bold`. El vídeo de xG actual añade sus fuentes y licencia musical; para otros vídeos, adaptar esos créditos a los materiales realmente usados.
