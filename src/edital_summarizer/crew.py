from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict
import yaml
from pathlib import Path
import json

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class EditalSummarizer:
    """EditalSummarizer crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"], verbose=True  # type: ignore[index]
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_analyst"],  # type: ignore[index]
            verbose=True,
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],  # type: ignore[index]
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config["reporting_task"],  # type: ignore[index]
            output_file="report.md",
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EditalSummarizer crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )


class DocumentSummarizerCrew:
    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"
        self.agents = self._load_agents()

    def _load_agents(self) -> Dict[str, Agent]:
        with open(self.config_dir / "agents.yaml") as f:
            agents_config = yaml.safe_load(f)

        return {name: Agent(**config) for name, config in agents_config.items()}

    def _load_tasks(self) -> Dict[str, dict]:
        with open(self.config_dir / "tasks.yaml") as f:
            return yaml.safe_load(f)

    def extract_metadata(self, text: str) -> Dict:
        """Extract metadata from document text."""
        tasks_config = self._load_tasks()

        task = Task(
            description=tasks_config["metadata_extraction"]["description"],
            agent=self.agents["metadata_agent"],
        )

        crew = Crew(agents=[self.agents["metadata_agent"]], tasks=[task], verbose=True)

        result = crew.kickoff()
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to parse metadata"}

    def generate_summary(self, text: str, summary_type: str) -> str:
        """Generate a summary of the specified type."""
        tasks_config = self._load_tasks()

        if summary_type == "executivo":
            agent = self.agents["executive_summary_agent"]
            task_config = tasks_config["executive_summary"]
        elif summary_type == "técnico":
            agent = self.agents["technical_summary_agent"]
            task_config = tasks_config["technical_summary"]
        else:
            raise ValueError(f"Unknown summary type: {summary_type}")

        task = Task(
            description=f"{task_config['description']}\n\nDocument text:\n{text}",
            agent=agent,
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=True)

        return crew.kickoff()

    def process_document(self, text: str, summary_types: List[str] = None) -> Dict:
        """Process a document and generate all requested summaries."""
        if summary_types is None:
            summary_types = ["executivo", "técnico"]

        result = {"metadata": self.extract_metadata(text), "summaries": {}}

        for summary_type in summary_types:
            result["summaries"][summary_type] = self.generate_summary(
                text, summary_type
            )

        return result
