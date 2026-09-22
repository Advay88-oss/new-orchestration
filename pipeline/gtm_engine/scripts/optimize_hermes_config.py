import yaml
from pathlib import Path

cfg_path = Path("C:/Users/Advay Anand/AppData/Local/hermes/config.yaml")
cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

# 1. Turn budget cap
cfg["agent"]["max_turns"] = 25

# 2. Context compression and proactive pruning
cfg["compression"]["threshold"] = 0.35
cfg["compression"]["proactive_prune_tokens"] = 2048
cfg["compression"]["proactive_prune_min_result_chars"] = 4000
cfg["compression"]["idle_compact_after_seconds"] = 180

# 3. Guardrails hard-stop
cfg["tool_loop_guardrails"]["hard_stop_enabled"] = True
cfg["tool_loop_guardrails"]["hard_stop_after"] = {
    "exact_failure": 3,
    "same_tool_failure": 4,
    "idempotent_no_progress": 3
}

# 4. Model output ceiling and primary model
cfg["model"]["default"] = "google/gemini-2.5-flash"
cfg["model"]["max_tokens"] = 1500

cfg_path.write_text(yaml.dump(cfg, sort_keys=False), encoding="utf-8")
print("CONFIG_OPTIMIZED_SUCCESS")
