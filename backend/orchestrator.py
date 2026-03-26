from lead_intelligence import collect_lead_intelligence
from agent.psychology import analyze_psychology
from agent.objections import predict_objections
from agent.strategy import build_closing_strategy
from agent.scripts import generate_scripts
from agent.report import compile_report

class ClosureAgentOrchestrator:
    def __init__(self):
        self.current_step = 0
        self.total_steps  = 6

    def run(self, data):
        try:
            # Step 1: Lead Intelligence (6 layers + synthesis)
            self.current_step = 1
            lead_info = collect_lead_intelligence(data)

            # Attach intelligence to data so agents can access synthesis + past_memory
            data._intelligence = lead_info

            # Step 2: Psychology Analysis
            self.current_step = 2
            psychology = analyze_psychology(lead_info, data)

            # Step 3: Objection Prediction
            self.current_step = 3
            objections = predict_objections(psychology, data)

            # Step 4: Closing Strategy
            self.current_step = 4
            strategy = build_closing_strategy(psychology, objections, data)

            # Step 5: Script Generation
            self.current_step = 5
            scripts = generate_scripts(psychology, objections, strategy, data)

            # Step 6: Report Compilation
            self.current_step = 6
            report = compile_report(lead_info, psychology, objections, strategy, scripts)

            return report

        except Exception as e:
            raise Exception(f"Workflow failed at step {self.current_step}: {str(e)}")

    def get_progress(self):
        return {
            "current_step":        self.current_step,
            "total_steps":         self.total_steps,
            "progress_percentage": (self.current_step / self.total_steps) * 100
        }
