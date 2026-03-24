import json
from pathlib import Path

from jinja2 import Template


def generate_html_report(report, output_path="reports/mqa_report.html"):
    """
    Genera un informe HTML a partir del reporte MQA + SHACL.
    """

    # -------------------------------------------------------
    # Preparación del entorno
    # -------------------------------------------------------
    tpl_path = Path(__file__).resolve().parent / "templates" / "report_template.html"
    tpl_str = tpl_path.read_text(encoding="utf-8")

    tmpl = Template(tpl_str)

    # -------------------------------------------------------
    # Datos a pasar a la plantilla
    # -------------------------------------------------------
    summary = report["summary"]
    metrics = report["metrics_detail"]
    shacl = report["SHACL_validation"]

    dimension_labels = [d["dimension"] for d in summary["dimensions"]]
    dimension_scores = [d["score"] for d in summary["dimensions"]]

    rendered = tmpl.render(
        MQA_total=summary["MQA_total_score"],
        MQA_max=summary["MQA_max_score"],
        passed=metrics["passed"],
        failed=metrics["failed"],
        shacl=shacl,
        dimension_labels=json.dumps(dimension_labels),
        dimension_scores=json.dumps(dimension_scores),
    )

    # -------------------------------------------------------
    # Guardar archivo
    # -------------------------------------------------------
    out_path = Path(output_path)
    out_path.parent.mkdir(exist_ok=True)

    out_path.write_text(rendered, encoding="utf-8")

    return str(out_path)