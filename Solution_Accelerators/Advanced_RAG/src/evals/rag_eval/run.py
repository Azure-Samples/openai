from config import DefaultConfig
from evaluation_params import get_arguments
from flows.end_to_end_eval_flow import EndToEndEvalFlow
from flows.fanout_rephraser_eval_flow import FanoutRephraserEvaluationFlow
from flows.tone_eval_flow import ToneEvalFlow

DefaultConfig.initialize()

if __name__ == "__main__":
    print(r"""
           ___          _
          | __|_ ____ _| |
          | _|\ V / _` | |
          |___|\_/\__,_|_|
          """)
    eval_params = get_arguments()
    if eval_params.eval_flow == "evaluate_end_to_end":
        end_to_end_flow = EndToEndEvalFlow(eval_params)
        end_to_end_flow.evaluate()
    else:
        raise ValueError(f"Unknown evaluation flow: {eval_params.eval_flow}")
    print("=" * 120)
    print("Done!")