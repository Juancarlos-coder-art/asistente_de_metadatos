def build_report(score, metrics, shacl_results):
    """
    Genera un informe completo combinando:
    - MQA (métricas de calidad)
    - SHACL (conformidad estructural)
    - Resumen por dimensiones
    
    Parámetros:
        score (int): puntuación total de MQA
        metrics (list): lista de métricas evaluadas por QualityValidator
        shacl_results (list): lista de (shape_file, result_dict)

    Devuelve:
        dict: informe completo
    """

    # ------------------------------------------------------------
    # 1. Métricas aprobadas / falladas
    # ------------------------------------------------------------
    passed = [m for m in metrics if m["passed"]]
    failed = [m for m in metrics if not m["passed"]]

    # ------------------------------------------------------------
    # 2. Puntuación por dimensión (Findability, Interoperability, etc.)
    # ------------------------------------------------------------
    dimensions = {}
    for m in metrics:
        dim = m.get("dimension", "Unknown")
        if dim not in dimensions:
            dimensions[dim] = {"score": 0, "metrics": 0}

        dimensions[dim]["metrics"] += 1
        if m["passed"]:
            dimensions[dim]["score"] += m.get("weight", 0)

    # Preparar un formato homogéneo
    dimensions_summary = [
        {
            "dimension": k,
            "score": v["score"],
            "max_score": sum(
                m.get("weight", 0)
                for m in metrics
                if m.get("dimension") == k
            ),
            "metrics_count": v["metrics"]
        }
        for k, v in dimensions.items()
    ]

    # ------------------------------------------------------------
    # 3. SHACL resumen
    # ------------------------------------------------------------
    shacl_summary = []
    for shape_name, result in shacl_results:
        shacl_summary.append({
            "shape": shape_name,
            "conforms": result.get("conforms", False),
            "report": result.get("report", "")
        })

    # ------------------------------------------------------------
    # 4. Resumen final
    # ------------------------------------------------------------
    return {
        "summary": {
            "MQA_total_score": score,
            "MQA_max_score": sum(m.get("weight", 0) for m in metrics),
            "MQA_passed_metrics": len(passed),
            "MQA_failed_metrics": len(failed),
            "dimensions": dimensions_summary,
        },
        "metrics_detail": {
            "passed": passed,
            "failed": failed,
            "all_metrics": metrics
        },
        "SHACL_validation": shacl_summary
    }
