"""
Background Task Runner

Async background task execution for long-running agent workflows.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import get_settings
from app.models import AgentRun, Artifact

logger = logging.getLogger(__name__)
settings = get_settings()


async def get_async_session() -> AsyncSession:
    """Create a new async database session for background tasks."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session()


async def run_discovery_agent(run_id: str, project_id: str, query: str) -> None:
    """
    Execute the discovery agent pipeline in the background.
    """
    from app.agents import create_discovery_graph
    
    logger.info(f"[DISCOVERY] Starting discovery agent for run {run_id}")
    logger.info(f"[DISCOVERY] Query: {query}")
    
    db = await get_async_session()
    
    try:
        # Update run status to running
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            logger.error(f"[DISCOVERY] Run {run_id} not found")
            return
        
        run.status = "running"
        run.started_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[DISCOVERY] Run status updated to 'running'")
        
        # Create and execute the discovery graph
        graph = create_discovery_graph()
        
        initial_state = {
            "user_query": query,
            "project_id": project_id,
            "domain_boundaries": {},
            "search_queries": [],
            "constraints": {},
            "papers": [],
            "themes": [],
            "trends": {},
            "gaps": [],
            "directions": [],
            "current_step": "starting",
            "error": None,
            "messages": [],
        }
        
        logger.info(f"[DISCOVERY] Executing graph pipeline...")
        
        # Execute the graph
        final_state = await graph.ainvoke(initial_state)
        
        logger.info(f"[DISCOVERY] Graph execution completed")
        logger.info(f"[DISCOVERY] Current step: {final_state.get('current_step')}")
        
        # Check for error in state
        if final_state.get("error"):
            logger.error(f"[DISCOVERY] Pipeline error: {final_state['error']}")
            run.status = "failed"
            run.error_message = final_state["error"]
        else:
            # Extract directions and format result
            directions = final_state.get("directions") or []
            gaps = final_state.get("gaps") or []
            papers = final_state.get("papers") or []
            
            logger.info(f"[DISCOVERY] Found {len(papers)} papers, {len(gaps)} gaps, {len(directions)} directions")
            
            # Format directions with additional context
            formatted_directions = []
            for d in directions[:5]:  # Limit to 5
                formatted_directions.append({
                    "id": d.get("id", str(len(formatted_directions) + 1)),
                    "title": d.get("title", "Untitled Direction"),
                    "description": d.get("description", ""),
                    "past_approaches": d.get("novelty_angle", "Analysis pending..."),
                    "current_state": f"Based on analysis of {len(papers)} papers",
                    "gaps": ", ".join([g.get("description", "")[:100] for g in gaps[:2]]) if gaps else "See detailed report",
                    "improvements": d.get("expected_outcomes", ["Improvements identified"])[0] if d.get("expected_outcomes") else "See experiment plan",
                    "feasibility_score": d.get("feasibility_score", 7),
                    "contribution_type": d.get("contribution_type", "method"),
                    "minimum_experiments": d.get("minimum_experiments", []),
                })
            
            run.status = "completed"
            run.result = {
                "message": f"Discovery analysis complete for '{query}'",
                "field_overview": f"Analyzed {len(papers)} papers in {final_state.get('domain_boundaries', {}).get('field', 'the field')}",
                "directions": formatted_directions,
                "papers_analyzed": len(papers),
                "gaps_found": len(gaps),
                "themes": final_state.get("themes") or [],
                "domain_boundaries": final_state.get("domain_boundaries", {}),
            }
        
        run.finished_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[DISCOVERY] Run {run_id} completed with status: {run.status}")
        
    except Exception as e:
        logger.exception(f"[DISCOVERY] Unexpected error: {e}")
        try:
            result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = datetime.utcnow()
                await db.commit()
        except:
            pass
    finally:
        await db.close()


async def run_deep_dive_agent(run_id: str, project_id: str, direction: dict) -> None:
    """
    Execute the deep dive agent pipeline in the background.
    
    Args:
        run_id: The AgentRun ID to update
        project_id: The project this run belongs to
        direction: The selected research direction
    """
    from app.agents import create_deep_dive_graph

    logger.info(f"[DEEP_DIVE] Starting deep dive for run {run_id}")
    logger.info(f"[DEEP_DIVE] Direction: {direction.get('title', 'Unknown')}")
    
    db = await get_async_session()
    
    try:
        # Update run status
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            logger.error(f"[DEEP_DIVE] Run {run_id} not found")
            return
        
        run.status = "running"
        run.started_at = datetime.utcnow()
        await db.commit()
        
        # Create and execute the deep dive graph
        graph = create_deep_dive_graph()
        
        initial_state = {
            "project_id": project_id,
            "direction": direction,
            "baseline_methods": None,
            "metrics": None,
            "failure_cases": None,
            "hypotheses": None,
            "ablations": None,
            "training_protocol": None,
            "evaluation_plan": None,
            "compute_estimate": None,
            "current_step": "starting",
            "error": None,
            "messages": [],
        }
        
        logger.info(f"[DEEP_DIVE] Executing graph pipeline...")
        final_state = await graph.ainvoke(initial_state)
        
        logger.info(f"[DEEP_DIVE] Graph execution completed")
        
        if final_state.get("error"):
            logger.error(f"[DEEP_DIVE] Pipeline error: {final_state['error']}")
            run.status = "failed"
            run.error_message = final_state["error"]
        else:
            run.status = "completed"
            run.result = {
                "message": f"Deep dive complete for '{direction.get('title', 'Unknown')}'",
                "direction": direction,
                "baseline_methods": final_state.get("baseline_methods", []),
                "datasets": final_state.get("datasets", []),
                "metrics": final_state.get("metrics", []),
                "hypotheses": final_state.get("hypotheses", []),
                "ablations": final_state.get("ablations", []),
                "training_protocol": final_state.get("training_protocol", {}),
                "evaluation_plan": final_state.get("evaluation_plan", {}),
                "compute_estimate": final_state.get("compute_estimate", {}),
            }
            
            # Create an artifact with the experiment plan
            artifact = Artifact(
                project_id=project_id,
                artifact_type="experiment_plan",
                title=f"Experiment Plan: {direction.get('title', 'Research Direction')}",
                content_markdown=_format_experiment_plan(final_state),
            )
            db.add(artifact)
        
        run.finished_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[DEEP_DIVE] Run {run_id} completed with status: {run.status}")
        
    except Exception as e:
        logger.exception(f"[DEEP_DIVE] Unexpected error: {e}")
        try:
            result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = "failed"
                run.error_message = str(e)
                run.finished_at = datetime.utcnow()
                await db.commit()
        except:
            pass
    finally:
        await db.close()


def _format_experiment_plan(state: dict) -> str:
    """Format the experiment plan as markdown."""
    md = "# Experiment Plan\n\n"
    
    if state.get("hypotheses"):
        md += "## Hypotheses\n\n"
        for i, h in enumerate(state["hypotheses"], 1):
            if isinstance(h, dict):
                md += f"{i}. **{h.get('statement', '')}**\n"
                md += f"   - *Rationale*: {h.get('rationale', '')}\n"
            else:
                md += f"{i}. {h}\n"
        md += "\n"
    
    if state.get("baseline_methods"):
        md += "## Baseline Methods\n\n"
        for method in state["baseline_methods"]:
            md += f"- **{method.get('name', 'Unknown')}**: {method.get('description', '')}\n"
        md += "\n"
    
    if state.get("datasets"):
        md += "## Datasets\n\n"
        for ds in state["datasets"]:
            md += f"- **{ds.get('name', 'Unknown')}**: {ds.get('description', '')}\n"
        md += "\n"
    
    if state.get("metrics"):
        md += "## Evaluation Metrics\n\n"
        for metric in state["metrics"]:
            if isinstance(metric, dict):
                md += f"- **{metric.get('name', 'Metric')}**: {metric.get('description', '')}\n"
            else:
                md += f"- {metric}\n"
        md += "\n"
    
    if state.get("training_protocol"):
        md += "## Training Protocol\n\n"
        protocol = state["training_protocol"]
        md += f"- **Optimizer**: {protocol.get('optimizer', 'Adam')}\n"
        md += f"- **Learning Rate**: {protocol.get('learning_rate', '1e-4')}\n"
        md += f"- **Batch Size**: {protocol.get('batch_size', 32)}\n"
        md += f"- **Epochs**: {protocol.get('epochs', 100)}\n"
    
    if state.get("ablations"):
        md += "## Ablation Studies\n\n"
        for abl in state["ablations"]:
            md += f"- **{abl.get('name', 'Ablation')}**: {abl.get('description', '')}\n"
        md += "\n"
        
    md += "## Next Steps\n\n"
    md += "1. Review the experimental plan above.\n"
    md += "2. Execute the experiments locally or on your cluster.\n"
    md += "3. Upload the results (JSON, CSV, or log files) using the 'Upload Results' button below to proceed with the paper draft.\n"
    
    return md


async def run_paper_agent(run_id: str, project_id: str, direction: dict, experiment_data: list) -> None:
    """
    Execute the paper drafting agent pipeline in the background.
    """
    from app.agents import create_paper_graph

    logger.info(f"[PAPER] Starting paper generation for run {run_id}")
    logger.info(f"[PAPER] Processing {len(experiment_data)} uploaded files: {experiment_data}")
    
    db = await get_async_session()
    
    try:
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            return
        
        run.status = "running"
        run.started_at = datetime.utcnow()
        await db.commit()
        
        # Create and execute the paper graph
        graph = create_paper_graph()
        
        # Fetch context from previous runs
        deep_dive_report = ""
        loaded_experiment_data = []
        try:
            # Get deep dive run result
            deep_dive_run_result = await db.execute(
                select(AgentRun)
                .where(
                    AgentRun.project_id == project_id,
                    AgentRun.run_type == "deep_dive",
                    AgentRun.status == "completed"
                )
                .order_by(AgentRun.created_at.desc())
                .limit(1)
            )
            deep_dive_run = deep_dive_run_result.scalar_one_or_none()
            
            if deep_dive_run and deep_dive_run.result:
                # Reconstruct report from result fields
                res = deep_dive_run.result
                direction = res.get("direction", direction)
                
                # Build a summary string for the agent
                deep_dive_report = f"""
                Research Direction: {direction.get('title', 'Unknown')}
                Description: {direction.get('description', '')}
                
                Hypotheses: {json.dumps(res.get('hypotheses', []), indent=2)}
                Baseline Methods: {json.dumps(res.get('baseline_methods', []), indent=2)}
                Datasets: {json.dumps(res.get('datasets', []), indent=2)}
                Metrics: {json.dumps(res.get('metrics', []), indent=2)}
                Training Protocol: {json.dumps(res.get('training_protocol', {}), indent=2)}
                """
                
            # Get experiment file contents
            if experiment_data:
                from app.models import ExperimentUpload
                import aiofiles
                
                for exp_id in experiment_data:
                    # Fetch file record
                    exp_result = await db.execute(
                        select(ExperimentUpload).where(ExperimentUpload.id == exp_id)
                    )
                    exp_record = exp_result.scalar_one_or_none()
                    
                    if exp_record:
                        try:
                            # Use regular open for reading if async fails or for simplicity
                            with open(exp_record.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                loaded_experiment_data.append({
                                    "name": exp_record.original_name,
                                    "type": exp_record.file_type,
                                    "content": content
                                })
                        except Exception as e:
                            logger.error(f"[PAPER] Failed to read experiment file {exp_id}: {e}")
            
            logger.info(f"[PAPER] Context loaded. Report length: {len(deep_dive_report)}, Experiment files: {len(loaded_experiment_data)}")

        except Exception as e:
            logger.error(f"[PAPER] Error fetching context: {e}")
            
        
        initial_state = {
            "project_id": project_id,
            "direction": direction,
            "deep_dive_report": deep_dive_report,
            "experiment_data": loaded_experiment_data,
            "outline": None,
            "title": None,
            "abstract": None,
            "introduction": None,
            "related_work": None,
            "method": None,
            "experiments": None,
            "results": None,
            "discussion": None,
            "conclusion": None,
            "references": None,
            "paper_markdown": None,
            "current_step": "starting",
            "error": None,
            "messages": [],
        }
        
        logger.info(f"[PAPER] Executing graph pipeline with {len(loaded_experiment_data)} result files...")
        final_state = await graph.ainvoke(initial_state)
        
        if final_state.get("error"):
            run.status = "failed"
            run.error_message = final_state["error"]
        else:
            run.status = "completed"
            
            paper_markdown = final_state.get("paper_markdown", "")
            
            run.result = {
                "message": "Paper draft generated",
                "title": final_state.get("title", "Research Paper"),
                "sections": {
                    "abstract": final_state.get("abstract"),
                    "introduction": final_state.get("introduction"),
                    "related_work": final_state.get("related_work"),
                    "method": final_state.get("method"),
                    "experiments": final_state.get("experiments"),
                    "results": final_state.get("results"),
                    "discussion": final_state.get("discussion"),
                    "conclusion": final_state.get("conclusion"),
                },
            }
            
            # Create paper artifact
            artifact = Artifact(
                project_id=project_id,
                artifact_type="paper_draft",
                title=final_state.get("title", "Research Paper Draft"),
                content_markdown=paper_markdown,
            )
            db.add(artifact)
        
        run.finished_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[PAPER] Run {run_id} completed")
        
    except Exception as e:
        logger.exception(f"[PAPER] Unexpected error: {e}")
    finally:
        await db.close()
