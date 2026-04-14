from lead_intelligence import collect_lead_intelligence
from agent.psychology import analyze_psychology
from agent.objections import predict_objections
from agent.strategy import build_closing_strategy
from agent.scripts import generate_scripts
from agent.report import compile_report
from agent.reflection import critique_psychology, critique_scripts, critique_report
import json
 
class ClosureAgentOrchestrator:
    def __init__(self):
        self.current_step = 0
        self.total_steps  = 6
 
    def stream(self, data):
        """Generator — yields progress events then final report as NDJSON lines"""
        def emit(event: str, message: str, payload: dict = None):
            line = {"event": event, "step": self.current_step, "total": self.total_steps, "message": message}
            if payload:
                line["data"] = payload
            return json.dumps(line) + "\n"
 
        try:
            # Step 1: Lead Intelligence
            self.current_step = 1
            yield emit("progress", "🔍 Scraping website, news, YouTube & Trustpilot...")
            lead_info = collect_lead_intelligence(data)
            data._intelligence = lead_info
            yield emit("progress", f"✅ Intelligence gathered — score: {lead_info.get('intelligence_score', 0)}/100")
 
            # Step 2: Psychology + Reflection Point 1
            self.current_step = 2
            yield emit("progress", "🧠 Analysing client psychology...")
            psychology = analyze_psychology(lead_info, data)
 
            critique = critique_psychology(psychology, lead_info, data)
            reflection = critique.get("_reflection", {})
            if reflection.get("retried"):
                yield emit("progress", f"🔄 Psychology refined — score was {reflection.get('original_score')}/10, retried")
                psychology = critique  # critique_psychology returns the improved dict directly
            else:
                yield emit("progress", f"✅ Psychology profile ready — score {reflection.get('score', '?')}/10")
 
            # Step 3: Objection Prediction
            self.current_step = 3
            yield emit("progress", "⚠️ Predicting objections & rebuttals...")
            objections = predict_objections(psychology, data)
            yield emit("progress", "✅ Objections mapped")
 
            # Step 4: Closing Strategy
            self.current_step = 4
            yield emit("progress", "🎯 Building closing strategy...")
            strategy = build_closing_strategy(psychology, objections, data)
            yield emit("progress", "✅ Closing strategy ready")
 
            # Step 5: Scripts + Reflection Point 2
            self.current_step = 5
            yield emit("progress", "🗣 Writing personalised call scripts...")
            scripts = generate_scripts(psychology, objections, strategy, data)
 
            scripts = critique_scripts(scripts, lead_info, psychology, strategy, objections, data)
            script_reflection = scripts.get("_reflection", {})
            fields_rewritten = script_reflection.get("fields_rewritten", [])
            if fields_rewritten:
                yield emit("progress", f"🔄 Scripts refined — rewrote: {', '.join(fields_rewritten)}")
            else:
                yield emit("progress", f"✅ Scripts ready — score {script_reflection.get('score', '?')}/10")
 
            # Step 6: Report + Reflection Point 3
            self.current_step = 6
            yield emit("progress", "📋 Compiling final report...")
            report = compile_report(lead_info, psychology, objections, strategy, scripts)
 
            consistency = critique_report(report)
            report["consistency_check"] = consistency
 
            flags = consistency.get("flags", [])
            if flags:
                flag_summary = f"{len(flags)} issue(s) flagged"
                yield emit("progress", f"⚠️ Consistency check: {flag_summary} — {consistency.get('summary', '')}")
            else:
                yield emit("progress", f"✅ Consistency check passed — {consistency.get('summary', '')}")
 
            yield emit("done", "🎉 Report ready!", {"closure_report": report})
 
        except Exception as e:
            yield emit("error", f"Workflow failed at step {self.current_step}: {str(e)}")