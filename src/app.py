"""Run from the repository root: python3 -m streamlit run src/app.py"""
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import APIError, OpenAI
import streamlit as st

import bondscope
import evidence

LABELS = {
    "brief.md": "Задание участникам", "rubric.md": "Критерии жюри",
    "data_dictionary.md": "Словарь полей", "daily_summary.csv": "Дневная сводка",
    "trade_register.csv": "Реестр сделок",
}
STATUS = {"confirmed": "Проблема подтверждена", "no_issue": "Расхождений по критерию нет",
          "incomplete": "Проверка неполная"}
STYLE = """
<style>
[data-testid="stMainBlockContainer"] {max-width:1380px;padding:4rem clamp(1.2rem,4vw,4.4rem) 3rem}
[data-testid="stSidebar"] {background:#fff;border-right:1px solid #e0e6e2}
[data-testid="stSidebar"] h3 {font-size:1.04rem;margin:0}
[data-testid="stSidebar"] .stButton button {width:100%}
[data-testid="stMain"] h1 {font:700 clamp(1.9rem,3vw,2.65rem)/1.15 Inter,system-ui,sans-serif;
letter-spacing:-.045em;padding:.2rem 0 .45rem}
[data-testid="stMain"] h2 {font-size:1.48rem;letter-spacing:-.025em}
[data-testid="stMain"] h3 {font-size:1.04rem}
[data-testid="stMetric"] {background:#fff;border:1px solid #dce3de;border-radius:6px;
padding:.65rem .85rem;min-height:5.4rem}
[data-testid="stMetricValue"] {font-size:2rem;font-weight:550;font-variant-numeric:tabular-nums}
.stTabs [data-baseweb="tab-list"] {gap:1.25rem;border-bottom:1px solid #dce3de}
.stTabs [data-baseweb="tab"] {height:2.65rem}
.stTabs [aria-selected="true"] {color:#14764b}
[data-testid="stExpander"] {background:white;border-radius:6px}
@media(max-width:700px){[data-testid="stMainBlockContainer"]{padding:3.2rem 1rem 2rem}}
</style>
"""


def main():
    st.set_page_config(page_title="BondScope · Проверка кейса", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)
    load_dotenv(bondscope.ROOT / ".env")
    model = os.getenv("LLM_MODEL") or "gpt-4.1-mini"
    names = [item["file"] for item in bondscope.list_materials(bondscope.CASE)]
    folder = bondscope.ROOT / "cases" / bondscope.CASE
    version = (model, tuple((name, (folder / name).stat().st_mtime_ns) for name in names))
    if st.session_state.get("version") != version:
        st.session_state.pop("review", None)
        st.session_state.version = version

    with st.sidebar:
        st.subheader("Проверка кейса")
        st.caption("BondScope · учебный комплект")
        run_clicked = st.button("Проверить критерий", type="primary")
        st.divider()
        st.subheader("Фильтры материалов")
        kind = st.selectbox("Тип файла", ["Все материалы", "Документы", "Таблицы CSV"])
        options = [n for n in names if kind == "Все материалы"
                   or (n.lower().endswith(".csv") == (kind == "Таблицы CSV"))]
        selected = st.selectbox("Файл", [None] + options, format_func=lambda n: n or "Все файлы")
        st.caption("Фильтры управляют вкладками «Материалы» и «Источники».")
        st.divider()
        st.caption(f"Модель · {model}")

    st.title("BondScope")
    st.write("Проверка материалов хакатона перед публикацией")
    st.caption("Критерий: расчёт спреда  ·  Комплект участника: синтетические данные")
    if run_clicked:
        st.session_state.pop("review", None)
        key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not key:
            st.error("Для проверки добавьте LLM_API_KEY в файл .env проекта.")
        else:
            try:
                with st.spinner("Сопоставляем критерий и материалы…"):
                    with OpenAI(api_key=key, timeout=45, max_retries=1) as client:
                        st.session_state.review = evidence.review(client, model)
            except APIError as exc:
                st.error(f"Запрос к модели завершился ошибкой ({type(exc).__name__}).")
            except (OSError, ValueError) as exc:
                st.error(f"Не удалось подтвердить результат: {exc}")

    report = st.session_state.get("review")
    counts = [("Материалов в комплекте", len(names)), ("Критериев проверено", int(bool(report))),
              ("Проблем подтверждено", int(report["status"] == "confirmed") if report else "—"),
              ("Источников процитировано", len({x["file"] for x in report["evidence"]}) if report else "—")]
    for col, (label, value) in zip(st.columns(4), counts):
        col.metric(label, value)
    overview, materials, sources = st.tabs(["Проверка", "Материалы", "Источники"])
    visible = [selected] if selected else options
    with overview:
        st.subheader("Выполнимость критерия спреда")
        if report:
            color = {"confirmed": "orange", "incomplete": "violet", "no_issue": "green"}[report["status"]]
            st.badge(STATUS[report["status"]], color=color)
            if report["status"] == "confirmed":
                st.markdown("**Обязательный спред нельзя рассчитать по выданным материалам.**")
            st.write(report["finding"])
            st.markdown("**Влияние на оценку**")
            st.write(report["impact"])
            st.markdown("**Действие организатора**")
            st.write(report["next_action"])
        else:
            st.write(evidence.QUESTION)
            st.caption("Запустите проверку слева, чтобы получить вывод со ссылками на источники.")
        st.markdown("**Материалы проверки**")
        rows = [{"Материал": LABELS[n], "Файл": n,
                 "Состояние": ("В комплекте" if n in names else "Недоступен")}
                for n in evidence.DOCUMENTS + evidence.TABLES]
        st.dataframe(rows, hide_index=True, width="stretch")
    with materials:
        st.subheader("Материалы участника")
        if not visible:
            st.info("Нет файлов с выбранным типом.")
        for name in visible:
            with st.expander(f"{LABELS.get(name, name)} · {name}", expanded=bool(selected)):
                doc = evidence.find_evidence(bondscope.CASE, name, "")
                if doc["status"] != "found":
                    st.caption("Предпросмотр недоступен.")
                elif Path(name).suffix.lower() == ".csv":
                    st.caption("Заголовок CSV · строка 1")
                    st.code(doc["evidence"][0]["quote"], language=None)
                else:
                    for item in doc["evidence"]:
                        st.text(f"{item['line']:>2}   {item['quote']}")
    with sources:
        st.subheader("Основания вывода")
        if not report:
            st.caption("Цитаты появятся после проверки.")
        else:
            citations = [x for x in report["evidence"] if x["file"] in visible]
            if not citations:
                st.caption("Для выбранных материалов в отчёте нет цитат.")
            for name in dict.fromkeys(x["file"] for x in citations):
                with st.expander(f"{LABELS.get(name, name)} · {name}", expanded=bool(selected)):
                    for item in citations:
                        if item["file"] == name:
                            st.caption(f"Строка {item['line']}")
                            st.text(item["quote"])


if __name__ == "__main__":
    main()
