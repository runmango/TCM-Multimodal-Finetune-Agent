from __future__ import annotations

import html
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
import streamlit as st


DEFAULT_BACKEND_URL = "http://127.0.0.1:8010"
JSON_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json",
}
DISCLAIMER = (
    "本系统为技术演示版，仅用于中医知识检索、体质倾向分析和工程能力展示，"
    "不作为临床诊断依据。"
)


def normalize_base_url(base_url: str) -> str:
    return (base_url or DEFAULT_BACKEND_URL).strip().rstrip("/")


def make_url(base_url: str, path: str) -> str:
    clean_path = path if path.startswith("/") else "/%s" % path
    return "%s%s" % (normalize_base_url(base_url), clean_path)


def request_json(
    method: str,
    base_url: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 8.0,
) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    url = make_url(base_url, path)
    try:
        response = requests.request(
            method=method,
            url=url,
            json=payload,
            headers=JSON_HEADERS,
            timeout=timeout,
        )
    except requests.exceptions.ConnectionError as exc:
        return None, {
            "message": "后端服务未连接，请先启动 FastAPI 服务。",
            "detail": str(exc),
            "url": url,
        }
    except requests.exceptions.Timeout as exc:
        return None, {
            "message": "后端请求超时，请检查服务是否繁忙或地址是否正确。",
            "detail": str(exc),
            "url": url,
        }
    except requests.exceptions.RequestException as exc:
        return None, {
            "message": "请求后端服务失败。",
            "detail": str(exc),
            "url": url,
        }

    raw_text = response.text
    try:
        data = response.json() if raw_text else {}
    except ValueError as exc:
        return None, {
            "message": "后端返回内容不是合法 JSON。",
            "status_code": response.status_code,
            "detail": str(exc),
            "raw_text": raw_text[:1000],
            "url": url,
        }

    if response.status_code >= 400:
        status_message = {
            404: "接口不存在，请确认后端路由是否与页面配置一致。",
            500: "后端服务内部错误，请查看 FastAPI 日志。",
        }.get(response.status_code, "后端接口返回错误。")
        return None, {
            "message": status_message,
            "status_code": response.status_code,
            "detail": data,
            "url": url,
        }

    return data, None


@st.cache_data(ttl=5)
def check_backend(base_url: str) -> Tuple[bool, Dict[str, Any]]:
    health, health_error = request_json("GET", base_url, "/api/v1/health", timeout=2.0)
    if health_error is None:
        return True, {"endpoint": "/api/v1/health", "data": health}

    docs_url = make_url(base_url, "/docs")
    try:
        response = requests.get(docs_url, timeout=2.0)
        if response.status_code < 400:
            return True, {"endpoint": "/docs", "status_code": response.status_code}
        docs_error: Dict[str, Any] = {
            "message": "后端 /docs 可访问性检查失败。",
            "status_code": response.status_code,
            "url": docs_url,
        }
    except requests.exceptions.RequestException as exc:
        docs_error = {"message": "后端 /docs 不可访问。", "detail": str(exc), "url": docs_url}

    return False, {"health_error": health_error, "docs_error": docs_error}


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def safe_text(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return str(value)
    text = str(value).strip()
    return text if text else default


def render_error(error: Dict[str, Any]) -> None:
    st.warning(error.get("message", "请求失败，请稍后重试。"))
    with st.expander("技术详情"):
        st.json(error)


def render_tags(tags: Iterable[Any]) -> str:
    tag_items = [safe_text(tag) for tag in tags if safe_text(tag) != "-"]
    if not tag_items:
        return '<span class="tag muted">无标签</span>'
    return "".join('<span class="tag">%s</span>' % html.escape(tag) for tag in tag_items)


def render_result_card(item: Dict[str, Any], index: int) -> None:
    title = safe_text(item.get("title") or item.get("name") or "参考知识 %s" % index)
    content = safe_text(item.get("content") or item.get("text") or item.get("answer"))
    tags = ensure_list(item.get("tags") or item.get("labels"))
    score = item.get("score", "-")
    source_type = safe_text(item.get("source_type") or item.get("type"))
    item_id = safe_text(item.get("id") or item.get("source_id"))

    try:
        score_text = "%.3f" % float(score)
    except (TypeError, ValueError):
        score_text = safe_text(score)

    st.markdown(
        """
        <div class="result-card">
          <div class="card-title">{title}</div>
          <div class="card-content">{content}</div>
          <div class="card-tags">{tags}</div>
          <div class="card-meta">
            <span>score: <strong>{score}</strong></span>
            <span>source_type: <strong>{source_type}</strong></span>
            <span>ID: <strong>{item_id}</strong></span>
          </div>
        </div>
        """.format(
            title=html.escape(title),
            content=html.escape(content),
            tags=render_tags(tags),
            score=html.escape(score_text),
            source_type=html.escape(source_type),
            item_id=html.escape(item_id),
        ),
        unsafe_allow_html=True,
    )


def render_inference_result(query: str, data: Dict[str, Any]) -> None:
    safety = data.get("safety") or {}
    constitution = safe_text(
        data.get("constitution") or data.get("constitution_type") or data.get("label"),
        "无法判断",
    )
    answer = safe_text(
        data.get("answer") or data.get("analysis") or data.get("conclusion"),
        "后端未返回分析结论。",
    )
    confidence = data.get("confidence", "-")
    symptoms = ensure_list(data.get("symptoms") or data.get("matched_symptoms"))
    evidence = ensure_list(data.get("evidence") or data.get("results") or data.get("references"))
    disclaimer = safe_text(data.get("disclaimer"), DISCLAIMER)

    st.info("查询内容：%s" % query)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("体质倾向", constitution)
    col_b.metric("置信度", safe_text(confidence))
    col_c.metric("安全状态", safe_text(safety.get("status"), "unknown"))

    if safety.get("status") == "refused":
        st.warning(answer)
    elif constitution != "无法判断":
        st.success(answer)
    else:
        st.info(answer)

    if safety:
        with st.expander("安全策略结果", expanded=safety.get("status") == "refused"):
            st.json(safety)

    st.subheader("匹配依据")
    if symptoms:
        st.write("、".join(safe_text(item) for item in symptoms))
    else:
        st.write("未返回明确症状匹配。")

    st.subheader("参考知识")
    if evidence:
        for index, item in enumerate(evidence, start=1):
            if isinstance(item, dict):
                render_result_card(item, index)
            else:
                st.write(item)
    else:
        st.info("暂无参考知识返回。")

    st.caption(disclaimer)


def render_dataset_result(data: Any) -> None:
    if isinstance(data, dict):
        status = safe_text(data.get("status"), "unknown")
        if status == "success":
            st.success("知识库构建完成。")
        else:
            st.info("知识库构建接口已返回结果。")

        summary = data.get("summary") or {}
        if isinstance(summary, dict) and summary:
            cols = st.columns(min(4, max(1, len(summary))))
            for index, (key, value) in enumerate(summary.items()):
                cols[index % len(cols)].metric(str(key), safe_text(value))

        with st.expander("完整接口返回", expanded=True):
            st.json(data)
        return

    st.write(data)


def setup_page() -> None:
    st.set_page_config(
        page_title="中医知识库与体质辨识演示系统",
        page_icon="+",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .main { background: #f7fbff; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1180px; }
        h1, h2, h3 { color: #114a7a; }
        .subtitle { color: #42637a; font-size: 1.08rem; margin-top: -0.4rem; margin-bottom: 1.2rem; }
        .result-card {
            background: #ffffff;
            border: 1px solid #d8e8f5;
            border-left: 5px solid #2f80c1;
            border-radius: 8px;
            padding: 16px 18px;
            margin: 12px 0;
            box-shadow: 0 2px 8px rgba(17, 74, 122, 0.06);
        }
        .card-title { color: #114a7a; font-weight: 700; font-size: 1.04rem; margin-bottom: 8px; }
        .card-content { color: #233645; line-height: 1.72; margin-bottom: 12px; }
        .card-tags { margin: 8px 0 10px; }
        .tag {
            display: inline-block;
            background: #e8f3fb;
            color: #15537f;
            border: 1px solid #c9e1f2;
            border-radius: 999px;
            padding: 2px 9px;
            margin: 0 6px 6px 0;
            font-size: 0.82rem;
        }
        .tag.muted { color: #697a86; background: #eef3f6; border-color: #dde7ed; }
        .card-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            color: #5f7485;
            font-size: 0.86rem;
            border-top: 1px solid #edf3f8;
            padding-top: 10px;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #d8e8f5;
            border-radius: 8px;
            padding: 12px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    setup_page()

    st.title("中医知识库与体质辨识演示系统")
    st.markdown(
        '<div class="subtitle">基于 RAG 的中医知识检索与体质倾向分析 Demo</div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("演示配置")
        backend_url = st.text_input("后端服务地址", value=DEFAULT_BACKEND_URL)
        top_k = st.slider("top_k 数量", min_value=1, max_value=10, value=3, step=1)
        if st.button("重新检测后端"):
            check_backend.clear()

        connected, check_detail = check_backend(normalize_base_url(backend_url))
        if connected:
            st.success("后端服务已连接")
            with st.expander("连通性详情"):
                st.json(check_detail)
        else:
            st.warning("后端服务未连接，请先启动 FastAPI 服务。")
            with st.expander("连通性详情"):
                st.json(check_detail)

        st.divider()
        st.caption(DISCLAIMER)

    tab_infer, tab_search, tab_build = st.tabs(["体质辨识", "知识库检索", "知识库构建"])

    with tab_infer:
        st.subheader("体质辨识")
        infer_query = st.text_area(
            "请输入症状、舌象或体质相关描述",
            value="我最近乏力气短，自汗，舌淡有齿痕，想了解体质倾向。",
            height=120,
        )
        if st.button("开始体质辨识", type="primary"):
            payload = {"query": infer_query, "top_k": top_k}
            with st.spinner("正在调用体质辨识接口..."):
                data, error = request_json("POST", backend_url, "/api/v1/infer/constitution", payload=payload)
            if error:
                render_error(error)
            elif isinstance(data, dict):
                render_inference_result(infer_query, data)
            else:
                st.info("接口已返回结果，但格式不是对象。")
                st.write(data)

    with tab_search:
        st.subheader("知识库检索")
        search_query = st.text_input("请输入检索关键词", value="乏力气短舌淡齿痕")
        if st.button("开始检索", type="primary"):
            payload = {"query": search_query, "top_k": top_k}
            with st.spinner("正在检索知识库..."):
                data, error = request_json("POST", backend_url, "/api/v1/rag/search", payload=payload)
            if error:
                render_error(error)
            else:
                results = ensure_list(data.get("results") if isinstance(data, dict) else data)
                if not results:
                    st.info("未检索到匹配结果。")
                else:
                    st.success("检索完成，共返回 %s 条结果。" % len(results))
                    for index, item in enumerate(results, start=1):
                        if isinstance(item, dict):
                            render_result_card(item, index)
                        else:
                            st.write(item)

    with tab_build:
        st.subheader("知识库构建")
        st.write("点击按钮后会调用后端数据集治理流水线，生成 SFT、MM-SFT 和数据质量报告。")
        if st.button("构建/刷新知识库", type="primary"):
            with st.spinner("正在构建知识库..."):
                data, error = request_json("POST", backend_url, "/api/v1/dataset/build", payload={})
            if error:
                render_error(error)
            else:
                render_dataset_result(data)

    st.divider()
    st.caption(DISCLAIMER)


if __name__ == "__main__":
    main()

