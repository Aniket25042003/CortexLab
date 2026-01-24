"""
Experiment Designer Agent Node

Designs a comprehensive experiment plan based on the deep dive analysis,
including hypotheses, ablations, training protocol, and evaluation plan.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings
from app.agents.state import DeepDiveState
from app.agents.utils import parse_json
import json
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


EXPERIMENT_DESIGN_PROMPT = """You are an expert research experiment designer. Based on the research direction and deep dive analysis, design a comprehensive experiment plan.

## Research Direction
Title: {direction_title}
Description: {direction_description}
Novelty Angle: {novelty_angle}
Contribution Type: {contribution_type}

## Deep Dive Analysis

### Baseline Methods:
{baselines_text}

### Standard Datasets:
{datasets_text}

### Evaluation Metrics:
{metrics_text}

### Known Failure Cases:
{failure_cases_text}

### Implementation Notes:
{implementation_notes}

---

Design a complete experiment plan that would result in a publishable contribution. Be specific and actionable.

Respond in JSON format:
{{
    "hypotheses": [
        {{
            "id": "H1",
            "statement": "Clear, testable hypothesis statement",
            "rationale": "Why this hypothesis makes sense",
            "expected_outcome": "What we expect to observe if true",
            "null_hypothesis": "What the alternative would mean"
        }}
    ],
    "proposed_method": {{
        "name": "Your proposed method name",
        "description": "Detailed description of the approach",
        "key_innovations": ["list of novel aspects"],
        "architecture_overview": "High-level architecture description",
        "components": [
            {{
                "name": "component name",
                "purpose": "what it does",
                "implementation_notes": "how to implement"
            }}
        ]
    }},
    "ablation_studies": [
        {{
            "name": "Ablation study name",
            "description": "What aspect is being tested",
            "variants": ["list of variants to compare"],
            "expected_insight": "What we expect to learn"
        }}
    ],
    "experiment_setup": {{
        "datasets": [
            {{
                "name": "dataset name",
                "purpose": "why this dataset",
                "preprocessing": "preprocessing steps",
                "splits": "train/val/test configuration"
            }}
        ],
        "baselines": [
            {{
                "name": "baseline name",
                "implementation": "how to implement or obtain",
                "configuration": "key hyperparameters"
            }}
        ],
        "metrics": [
            {{
                "name": "metric name",
                "primary": true,
                "rationale": "why this metric matters"
            }}
        ]
    }},
    "training_protocol": {{
        "framework": "PyTorch/TensorFlow/JAX",
        "optimizer": "optimizer choice and rationale",
        "learning_rate": {{
            "initial": "value",
            "schedule": "schedule type",
            "warmup": "warmup steps if any"
        }},
        "batch_size": "recommended batch size",
        "epochs": "expected epochs to convergence",
        "regularization": ["list of regularization techniques"],
        "augmentation": ["data augmentation if applicable"],
        "early_stopping": "early stopping criteria",
        "checkpointing": "when to save checkpoints"
    }},
    "evaluation_plan": {{
        "validation_strategy": "k-fold/holdout/etc",
        "statistical_tests": ["tests to use for significance"],
        "visualization": ["what to visualize"],
        "error_analysis": "how to analyze failures",
        "reproducibility": ["steps for reproducibility"]
    }},
    "compute_estimate": {{
        "gpu_type": "recommended GPU",
        "gpu_hours": "estimated training time",
        "memory_requirements": "VRAM needed",
        "storage_requirements": "disk space for data/checkpoints",
        "total_experiments": "number of runs needed"
    }},
    "timeline": {{
        "phase1_implementation": "X weeks",
        "phase2_experiments": "X weeks", 
        "phase3_analysis": "X weeks",
        "phase4_writing": "X weeks",
        "total": "total estimated time"
    }},
    "risks_and_mitigations": [
        {{
            "risk": "potential risk",
            "likelihood": "high/medium/low",
            "mitigation": "how to address"
        }}
    ]
}}
"""


async def experiment_designer_node(state: DeepDiveState) -> DeepDiveState:
    """
    Design experiments for the chosen research direction.
    
    Input: direction, baseline_methods, datasets, metrics, failure_cases
    Output: hypotheses, ablations, training_protocol, evaluation_plan, compute_estimate
    """
    direction = state.get("direction", {})
    baseline_methods = state.get("baseline_methods", [])
    datasets = state.get("datasets", [])
    metrics = state.get("metrics", [])
    failure_cases = state.get("failure_cases", [])
    implementation_notes = state.get("implementation_notes", {})
    
    if not direction:
        return {
            **state,
            "error": "No direction provided for experiment design",
            "current_step": "error",
        }
    
    # Format inputs for the prompt
    baselines_text = json.dumps(baseline_methods, indent=2) if baseline_methods else "No baselines identified yet"
    datasets_text = json.dumps(datasets, indent=2) if datasets else "No datasets identified yet"
    metrics_text = json.dumps(metrics, indent=2) if metrics else "No metrics identified yet"
    failure_cases_text = json.dumps(failure_cases, indent=2) if failure_cases else "No failure cases identified yet"
    impl_notes_text = json.dumps(implementation_notes, indent=2) if implementation_notes else "No implementation notes"
    
    from app.agents.llm_factory import get_llm
    llm = get_llm(model_name="kimi", temperature=0.4)
    
    prompt = ChatPromptTemplate.from_template(EXPERIMENT_DESIGN_PROMPT)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "direction_title": direction.get("title", "Unknown"),
            "direction_description": direction.get("description", ""),
            "novelty_angle": direction.get("novelty_angle", ""),
            "contribution_type": direction.get("contribution_type", "method"),
            "baselines_text": baselines_text,
            "datasets_text": datasets_text,
            "metrics_text": metrics_text,
            "failure_cases_text": failure_cases_text,
            "implementation_notes": impl_notes_text,
        })
        
        result = parse_json(response.content)
        
        return {
            **state,
            "hypotheses": result.get("hypotheses", []),
            "proposed_method": result.get("proposed_method", {}),
            "ablations": result.get("ablation_studies", []),
            "experiment_setup": result.get("experiment_setup", {}),
            "training_protocol": result.get("training_protocol", {}),
            "evaluation_plan": result.get("evaluation_plan", {}),
            "compute_estimate": result.get("compute_estimate", {}),
            "timeline": result.get("timeline", {}),
            "risks": result.get("risks_and_mitigations", []),
            "current_step": "experiments_designed",
            "messages": state.get("messages", []) + [
                {
                    "type": "agent_note",
                    "agent": "experiment_designer",
                    "content": f"Designed experiment plan with {len(result.get('hypotheses', []))} hypotheses, "
                              f"{len(result.get('ablation_studies', []))} ablation studies"
                }
            ]
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Experiment design failed: {str(e)}",
            "current_step": "error",
        }
