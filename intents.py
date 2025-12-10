import re
from database import query

# Palabras clave por intención
INTENCIONES = {
    "generar_descripcion_producto": [
        "descripcion de",
        "descripcion para",
        "genera descripcion",
        "genera una descripcion",
        "crear descripcion",
        "haz una descripcion",
        "necesito una descripcion",
        "quiero una descripcion",
        "descripcion producto",
        "como describo",
        "descripcion del producto"
    ],
    "productos_mas_comprados": [
        "productos mas comprados",
        "producto mas vendido",
        "mas vendidos",
        "lo mas top",
        "que es lo mas comprado",
        "producto mas comprado",
        "cuales son los mas comprados",
        "mas populares",
        "mas pedidos",
        "mas solicitados",
        "mas buscados",
        "top ventas",
        "top vendidos",
        "ranking de productos",
        "productos tendencia",
        "productos en tendencia"
    ],
    "productos_mas_resenas": [
        "productos con mas comentarios",
        "mas resenas",
        "mas reseñas",
        "productos con mas opiniones",
        "mas comentados",
        "mas feedback",
        "mas valorados por usuarios",
        "productos con muchas reseñas",
        "productos mas comentados"
    ],
    "productos_mejor_calificados": [
        "mejor calificados",
        "mejores calificaciones",
        "mejor puntuados",
        "productos con mejor rating",
        "productos con mejor puntuacion",
        "productos mejor valorados",
        "productos con mas estrellas",
        "calificacion mas alta",
        "top calificados"
    ],
    "vendedor_mas_publicaciones": [
        "vendedor con mas productos",
        "mas publicaciones",
        "vendedor tiene mas productos",
        "tiene mas productos",
        "mas productos registrados",
        "productos registrados",
        "que vendedor vende mas",
        "que vendedor tiene mas cosas",
        "quien publica mas",
        "vendedor con mas ventas publicadas",
        "vendedor con mas inventario",
        "vendedor mas grande",
        "vendedor con mas oferta"
    ],
    "buscar_producto_por_categoria": [
        "categoria",
        "categoria de",
        "productos de",
        "que hay en la categoria",
        "mostrar categoria",
        "busca categoria",
        "quiero ver productos de",
        "productos en categoria",
        "categoria llamada",
        "que categorias tienen",
        "hay productos de"
    ],
    "productos_mas_baratos": [
        "mas barato",
        "lo mas barato",
        "baratos",
        "económicos",
        "precio bajo",
        "lo mas economico",
        "productos baratos",
        "los mas baratos",
        "productos económicos",
        "menor precio"
    ],
    "productos_mas_caros": [
        "mas caro",
        "lo mas caro",
        "caros",
        "precio alto",
        "productos caros",
        "los mas caros",
        "lo mas costoso",
        "mas costosos",
        "mayor precio"
    ],
    "resenas_producto": [
        "opiniones",
        "comentarios de",
        "comentarios hay de",
        "comentarios sobre",
        "que comentarios",
        "reseñas de",
        "resenas de",
        "que opinan de",
        "que dicen de",
        "que han dicho de",
        "valoraciones de",
        "reviews de",
        "review de"
    ],
    "calificacion_vendedor": [
        "calificación del vendedor",
        "como califican al vendedor",
        "rating del vendedor",
        "opiniones del vendedor",
        "que tal es el vendedor",
        "qué tan bueno es el vendedor",
        "cómo lo califican",
        "reseñas del vendedor",
        "calificación de",
        "puntuación del vendedor",
        "estrellas del vendedor",
        "evaluación del vendedor"
    ],
    "productos_recientes": [
        "productos nuevos",
        "publicados esta semana",
        "recientes",
        "lo más nuevo",
        "nuevos productos",
        "últimos productos",
        "recién publicados",
        "recién subidos",
        "acabados de publicar",
        "novedades",
        "últimas novedades",
        "últimos agregados",
        "últimos añadidos",
        "subidos recientemente",
        "agregados recientemente",
        "lo último que subieron",
        "lo más reciente",
        "productos frescos",
        "lo último en la tienda",
        "que hay de nuevo",
        "mostrar productos nuevos",
        "quiero ver novedades",
        "última actualización",
        "nuevas publicaciones",
        "lo último publicado",
        "productos del día",
        "publicados hoy"
    ],
    "buscar_producto_por_nombre": [
        "buscar",
        "muéstrame",
        "muestrame",
        "hay",
        "mostrar producto",
        "producto llamado",
        "quiero ver",
        "buscar producto"
    ]
}

# Funciones para cada intención
def ejecutar_intencion(intencion, mensaje):

    mensaje = mensaje.lower().strip()

    # ---------------------- TOP VENTAS ----------------------
    if intencion == "productos_mas_comprados":
        return query("""
            SELECT p.nombre, SUM(pd.cantidad) AS total_vendidos
            FROM pedido_detalle pd
            INNER JOIN producto p ON pd.id_producto = p.id_producto
            GROUP BY p.id_producto
            ORDER BY total_vendidos DESC
            LIMIT 5;
        """)

    # ---------------------- MÁS RESEÑAS ----------------------
    if intencion == "productos_mas_resenas":
        return query("""
            SELECT p.nombre, COUNT(r.id_resena) AS total_resenas
            FROM resena r
            INNER JOIN producto p ON r.id_producto = p.id_producto
            GROUP BY p.id_producto
            ORDER BY total_resenas DESC
            LIMIT 5;
        """)

    # ---------------------- MEJOR CALIFICADOS ----------------------
    if intencion == "productos_mejor_calificados":
        return query("""
            SELECT p.nombre, AVG(r.estrellas) AS promedio_calificacion
            FROM resena r
            INNER JOIN producto p ON r.id_producto = p.id_producto
            GROUP BY p.id_producto
            ORDER BY promedio_calificacion DESC
            LIMIT 5;
        """)

    # ---------------------- VENDEDOR CON MÁS PUBLICACIONES ----------------------
    if intencion == "vendedor_mas_publicaciones":
        return query("""
            SELECT u.nombre, COUNT(p.id_producto) AS productos_publicados
            FROM usuario u
            INNER JOIN producto p ON u.id_usuario = p.id_usuario
            GROUP BY u.id_usuario
            ORDER BY productos_publicados DESC;""")
    # ---------------------- PRODUCTO POR NOMBRE ----------------------
    if intencion == "buscar_producto_por_nombre":
        palabra = re.sub(r"(buscar|muéstrame|muestrame|hay|quiero ver)", "", mensaje).strip()

        return query("""
            SELECT nombre, precio, descripcion
            FROM producto
            WHERE nombre LIKE %s
            LIMIT 10;
        """, (f"%{palabra}%",))

    # ---------------------- PRODUCTO POR CATEGORÍA ----------------------
    if intencion == "buscar_producto_por_categoria":
        match = re.search(r"(categoria|productos de)\s+(.*)", mensaje)
        categoria = match.group(2) if match else ""

        return query("""
            SELECT p.nombre, p.precio
            FROM producto p
            INNER JOIN categoria c ON p.id_categoria = c.id_categoria
            WHERE c.nombre_categoria LIKE %s
            LIMIT 10;
        """, (f"%{categoria}%",))

    # ---------------------- BARATOS ----------------------
    if intencion == "productos_mas_baratos":
        return query("""
            SELECT nombre, precio
            FROM producto
            ORDER BY precio ASC
            LIMIT 5;
        """)

    # ---------------------- CAROS ----------------------
    if intencion == "productos_mas_caros":
        return query("""
            SELECT nombre, precio
            FROM producto
            ORDER BY precio DESC
            LIMIT 5;
        """)

    # ---------------------- RESEÑAS DE UN PRODUCTO ----------------------
    if intencion == "resenas_producto":
        producto = mensaje.split("de")[-1].strip()

        return query("""
            SELECT r.estrellas, r.comentario
            FROM resena r
            INNER JOIN producto p ON r.id_producto = p.id_producto
            WHERE p.nombre LIKE %s
            LIMIT 10;
        """, (f"%{producto}%",))

    # ---------------------- CALIFICACIÓN DE UN VENDEDOR ----------------------
    if intencion == "calificacion_vendedor":
        vendedor = mensaje.split("vendedor")[-1].strip()

        return query("""
            SELECT u.nombre, AVG(r.estrellas) AS promedio_calificacion
            FROM resena r
            INNER JOIN usuario u ON r.id_usuario = u.id_usuario
            WHERE u.nombre LIKE %s
            GROUP BY u.id_usuario;
        """, (f"%{vendedor}%",))

    # ---------------------- PRODUCTOS RECIENTES ----------------------
    if intencion == "productos_recientes":
        return query("""
            SELECT nombre, fecha_publicacion
            FROM producto
            WHERE fecha_publicacion >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ORDER BY fecha_publicacion DESC;
        """)

    # ---------------------- DESCRIPCIÓN AUTOMÁTICA ----------------------
    if intencion == "generar_descripcion_producto":
        producto = mensaje
        for key in [
            "descripcion de", "descripcion para", "genera descripcion",
            "crear descripcion", "haz una descripcion"
        ]:
            producto = producto.replace(key, "")

        producto = producto.strip()

        if not producto:
            return {"producto_descripcion": None}

        return {"producto_descripcion": producto}

    return None