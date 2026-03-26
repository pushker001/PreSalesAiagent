import time

def compile_report(intelligence, psychology, objections, strategy, scripts):
    synthesis = intelligence.get("synthesis", {})
    return {
        "lead_info":           intelligence,
        "psychology":          psychology,
        "objections":          objections.get("likely_objections", []),
        "strategy":            strategy,
        "scripts":             scripts,
        "synthesis":           synthesis,
        "intelligence_score":  intelligence.get("intelligence_score", 0),
        "generated_at":        time.strftime("%Y-%m-%d %H:%M:%S")
    }
