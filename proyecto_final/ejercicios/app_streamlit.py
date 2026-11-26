"""Interfaz visual en Streamlit para el gestor de alertas de seguridad.

Permite subir un fichero CSV para analizar y gestionar sus alertas, o iniciar
un conjunto vacío desde cero y descargarlo actualizado.
Ejecución: streamlit run app_streamlit.py
"""

import io
import csv
import tempfile
from datetime import date
from pathlib import Path

import altair as alt
import streamlit as st

from alertas import (
    CAMPOS,
    ErrorDeIncidencias,
    PRIORIDADES,
    almacen,
    analisis,
    gestor,
    informes,
)

ICONO_PRIORIDAD = {
    "critica": "🔴 critica",
    "alta": "🟠 alta",
    "media": "🟡 media",
    "baja": "🟢 baja",
}

ICONO_ESTADO = {
    "abierta": "🆕 abierta",
    "en_curso": "⚙️ en_curso",
    "resuelta": "✅ resuelta",
    "cerrada": "🔒 cerrada",
}


def _cargar_desde_bytes(contenido: bytes) -> gestor.GestorIncidencias:
    """Valida y carga un CSV subido usando ``almacen.cargar``."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
        tmp.write(contenido)
        ruta_tmp = Path(tmp.name)

    try:
        alertas_cargadas = almacen.cargar(ruta_tmp)
        return gestor.GestorIncidencias(alertas_cargadas)
    finally:
        if ruta_tmp.exists():
            ruta_tmp.unlink()


def _exportar_a_csv(app_gestor: gestor.GestorIncidencias) -> bytes:
    """Serializa el estado actual del gestor a bytes CSV usando ``Alerta.a_fila()``."""
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=CAMPOS)
    escritor.writeheader()
    escritor.writerows(alerta.a_fila() for alerta in app_gestor)
    return buffer.getvalue().encode("utf-8")


def _formatear_tabla_visual(tabla):
    """Prepara una copia visual de la tabla con iconos y fechas legibles."""
    df_vis = tabla.copy()
    df_vis["prioridad"] = df_vis["prioridad"].map(lambda p: ICONO_PRIORIDAD.get(p, p))
    df_vis["estado"] = df_vis["estado"].map(lambda e: ICONO_ESTADO.get(e, e))
    df_vis["asignada_a"] = df_vis["asignada_a"].replace("", "—")
    df_vis["fecha_deteccion"] = df_vis["fecha_deteccion"].dt.strftime("%Y-%m-%d")
    df_vis["fecha_cierre"] = df_vis["fecha_cierre"].dt.strftime("%Y-%m-%d").fillna("—")
    return df_vis


def main() -> None:
    st.set_page_config(
        page_title="SOC · Gestor de Alertas",
        page_icon="🛡️",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
        div[data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.06);
            border: 1px solid rgba(128, 128, 128, 0.18);
            padding: 0.75rem 1rem;
            border-radius: 0.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "gestor_alertas_streamlit" not in st.session_state:
        st.session_state["gestor_alertas_streamlit"] = gestor.GestorIncidencias()
        st.session_state["archivo_cargado_id"] = None
        st.session_state["nombre_archivo_salida"] = "alertas_actualizadas.csv"

    with st.sidebar:
        st.header("📂 Archivo de alertas")
        archivo_subido = st.file_uploader(
            "Sube un archivo CSV",
            type=["csv"],
            help="Debe contener las columnas: " + ", ".join(CAMPOS),
        )

        if archivo_subido is not None:
            firma_archivo = (archivo_subido.name, archivo_subido.size)
            if st.session_state.get("archivo_cargado_id") != firma_archivo:
                try:
                    nuevo_gestor = _cargar_desde_bytes(archivo_subido.getvalue())
                    st.session_state["gestor_alertas_streamlit"] = nuevo_gestor
                    st.session_state["archivo_cargado_id"] = firma_archivo
                    st.session_state["nombre_archivo_salida"] = archivo_subido.name
                    st.toast(f"Cargado '{archivo_subido.name}'", icon="✅")
                except ErrorDeIncidencias as exc:
                    st.error(f"Error en el CSV: {exc}")

        if st.button("🧹 Iniciar vacío", use_container_width=True):
            st.session_state["gestor_alertas_streamlit"] = gestor.GestorIncidencias()
            st.session_state["archivo_cargado_id"] = None
            st.session_state["nombre_archivo_salida"] = "alertas_nuevas.csv"
            st.rerun()

        st.divider()
        app_gestor: gestor.GestorIncidencias = st.session_state["gestor_alertas_streamlit"]
        st.download_button(
            "⬇️ Descargar CSV actualizado",
            data=_exportar_a_csv(app_gestor),
            file_name=st.session_state["nombre_archivo_salida"],
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )

    app_gestor = st.session_state["gestor_alertas_streamlit"]
    hoy = date.today()
    tabla = analisis.a_tabla(app_gestor)
    metrics = analisis.indicadores(tabla, hoy=hoy)

    st.title("🛡️ Centro de Operaciones · Gestor de Alertas")
    st.caption(
        f"Archivo activo: `{st.session_state['nombre_archivo_salida']}` · "
        f"Total en sesión: **{len(app_gestor)}** alertas"
    )

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total alertas", metrics["total"])
    k2.metric("Pendientes", metrics["pendientes"])
    k3.metric("% Pendientes", f"{metrics['porcentaje_pendientes']}%")
    k4.metric("Sin asignar", metrics["sin_asignar"])
    k5.metric(
        "Media cierre",
        f"{metrics['dias_medios_resolucion']} d"
        if metrics["dias_medios_resolucion"] is not None
        else "—",
    )
    k6.metric("Antigüedad máx.", f"{metrics['antiguedad_maxima']} d")

    st.write("")

    tab_panel, tab_triaje, tab_analitica = st.tabs(
        ["📋 Bandeja de Alertas", "🛠️ Triaje y Acciones", "📈 Analítica SOC"]
    )

    with tab_panel:
        if len(app_gestor) == 0:
            st.info(
                "Sube un archivo CSV desde la barra lateral izquierda o registra una "
                "nueva alerta en la pestaña **Triaje y Acciones**."
            )
        else:
            with st.container(border=True):
                f1, f2, f3 = st.columns([3, 2, 1])
                texto_filtro = f1.text_input(
                    "Buscar por título u origen",
                    placeholder="Ej. SSH, 10.0.4.88, bastion...",
                )
                prio_filtro = f2.selectbox("Severidad", ["Todas", *PRIORIDADES])
                solo_pend = f3.checkbox("Solo pendientes", value=False)

            if solo_pend:
                base = app_gestor.pendientes()
                if texto_filtro.strip() or prio_filtro != "Todas":
                    ids_ok = {
                        a.id
                        for a in app_gestor.filtrar(
                            prioridad=None if prio_filtro == "Todas" else prio_filtro,
                            texto=texto_filtro if texto_filtro.strip() else None,
                        )
                    }
                    mostradas = [a for a in base if a.id in ids_ok]
                else:
                    mostradas = base
            else:
                mostradas = app_gestor.filtrar(
                    prioridad=None if prio_filtro == "Todas" else prio_filtro,
                    texto=texto_filtro if texto_filtro.strip() else None,
                )

            with st.container(border=True):
                st.subheader(f"Alertas visibles ({len(mostradas)})")
                if mostradas:
                    st.dataframe(
                        _formatear_tabla_visual(analisis.a_tabla(mostradas)),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No hay alertas que coincidan con los filtros actuales.")

            with st.expander("📄 Ver informe clásico en texto plano (78 columnas)"):
                st.code(informes.resumen(app_gestor, hoy), language="text")

    with tab_triaje:
        col_izq, col_der = st.columns(2)

        with col_izq:
            with st.container(border=True):
                st.subheader("➕ Registrar nueva alerta")
                with st.form("form_nueva_alerta", clear_on_submit=True):
                    titulo = st.text_input("Título de la alerta")
                    origen = st.text_input("Origen (IP, host o usuario)")
                    prioridad = st.selectbox("Prioridad", list(PRIORIDADES), index=1)
                    enviar = st.form_submit_button("Crear alerta", type="primary")

                if enviar:
                    try:
                        creada = app_gestor.crear(
                            titulo=titulo,
                            solicitante=origen,
                            prioridad=prioridad,
                            hoy=hoy,
                        )
                        st.success(f"Creada la alerta #{creada.id}.")
                        st.rerun()
                    except ErrorDeIncidencias as exc:
                        st.error(f"Error: {exc}")

        with col_der:
            with st.container(border=True):
                st.subheader("🎯 Gestión de alerta")
                todas = list(app_gestor)
                if not todas:
                    st.info("Todavía no hay alertas para gestionar.")
                else:
                    ids = [a.id for a in todas]
                    id_sel = st.selectbox(
                        "Alerta seleccionada",
                        options=ids,
                        format_func=lambda i: (
                            f"#{i} · {app_gestor.obtener(i).titulo} "
                            f"({ICONO_ESTADO[app_gestor.obtener(i).estado]})"
                        ),
                    )
                    alerta_sel = app_gestor.obtener(id_sel)
                    st.caption(
                        f"Origen: `{alerta_sel.origen}` · Prioridad: "
                        f"`{ICONO_PRIORIDAD[alerta_sel.prioridad]}` · "
                        f"Analista: `{alerta_sel.asignada_a or 'Sin asignar'}` · "
                        f"Días abierta: `{alerta_sel.dias_abierta(hoy)}`"
                    )

                    c_e1, c_e2 = st.columns([2, 1])
                    nuevo_estado = c_e1.selectbox(
                        "Cambiar estado a",
                        options=["abierta", "en_curso", "resuelta", "cerrada"],
                    )
                    if c_e2.button("Aplicar estado", use_container_width=True):
                        try:
                            app_gestor.cambiar_estado(id_sel, nuevo_estado, hoy=hoy)
                            st.success(f"Alerta #{id_sel} -> {nuevo_estado}")
                            st.rerun()
                        except ErrorDeIncidencias as exc:
                            st.error(f"Error: {exc}")

                    c_a1, c_a2 = st.columns([2, 1])
                    analista = c_a1.text_input("Asignar a analista", placeholder="Ej. Marta")
                    if c_a2.button("Asignar", use_container_width=True):
                        try:
                            asignada = app_gestor.asignar(id_sel, analista)
                            st.success(
                                f"Alerta #{id_sel} asignada a {asignada.asignada_a} "
                                f"({asignada.estado})."
                            )
                            st.rerun()
                        except ErrorDeIncidencias as exc:
                            st.error(f"Error: {exc}")
    with tab_analitica:
        if tabla.empty:
            st.info("No hay alertas suficientes para mostrar analítica.")
        else:
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                with st.container(border=True):
                    st.subheader("Alertas por prioridad")
                    conteo_prio = (
                        tabla["prioridad"]
                        .value_counts()
                        .reindex(list(reversed(PRIORIDADES)), fill_value=0)
                        .reset_index()
                    )
                    conteo_prio.columns = ["prioridad", "cantidad"]

                    grafico_prio = (
                        alt.Chart(conteo_prio)
                        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
                        .encode(
                            x=alt.X("cantidad:Q", title="Número de alertas"),
                            y=alt.Y("prioridad:N", sort=list(reversed(PRIORIDADES)), title="Prioridad"),
                            color=alt.Color(
                                "prioridad:N",
                                scale=alt.Scale(
                                    domain=["critica", "alta", "media", "baja"],
                                    range=["#d92d20", "#ef6820", "#eab308", "#16a34a"],
                                ),
                                legend=None,
                            ),
                            tooltip=["prioridad", "cantidad"],
                        )
                        .properties(height=240)
                    )
                    st.altair_chart(grafico_prio, use_container_width=True)

            with col_g2:
                with st.container(border=True):
                    st.subheader("Carga por analista")
                    res_tec = analisis.resumen_por_tecnico(tabla)
                    carga_analistas = res_tec[res_tec.index != "Sin asignar"]
                    if carga_analistas.empty:
                        st.info("Todavía no hay alertas asignadas a ningún analista.")
                    else:
                        st.dataframe(carga_analistas, use_container_width=True)

            with st.container(border=True):
                st.subheader("Matriz Estado × Prioridad")
                st.dataframe(analisis.tabla_estado_prioridad(tabla), use_container_width=True)

            with st.container(border=True):
                sin_asig_df = analisis.alertas_sin_asignar(tabla)
                st.subheader(f"Alertas sin asignar ({len(sin_asig_df)})")
                if sin_asig_df.empty:
                    st.success("Todas las alertas tienen un analista asignado.")
                else:
                    st.dataframe(sin_asig_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()