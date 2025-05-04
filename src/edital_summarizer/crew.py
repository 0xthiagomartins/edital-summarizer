from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict
import yaml
from pathlib import Path
import json
from rich import print as rprint
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    BarColumn,
)

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
    def __init__(self, language: str = "pt-br", verbose: bool = False):
        self.config_dir = Path(__file__).parent / "config"
        self.language = language
        self.verbose = verbose
        self.agents = self._load_agents()

    def _load_agents(self) -> Dict[str, Agent]:
        with open(self.config_dir / "agents.yaml") as f:
            agents_config = yaml.safe_load(f)

        # Process language-specific configurations
        for name, config in agents_config.items():
            if isinstance(config["goal"], dict):
                config["goal"] = config["goal"][self.language]
            if isinstance(config["backstory"], dict):
                config["backstory"] = config["backstory"][self.language]

        return {name: Agent(**config) for name, config in agents_config.items()}

    def _load_tasks(self) -> Dict[str, dict]:
        with open(self.config_dir / "tasks.yaml") as f:
            tasks_config = yaml.safe_load(f)

        # Process language-specific descriptions
        for task_name, task_config in tasks_config.items():
            if isinstance(task_config.get("description"), dict):
                task_config["description"] = task_config["description"][self.language]

        return tasks_config

    def extract_metadata(self, text: str) -> Dict:
        """Extract metadata from document text."""
        if self.verbose:
            rprint("[yellow]Starting metadata extraction...[/yellow]")
            rprint(f"[dim]Text length: {len(text)} characters[/dim]")

        tasks_config = self._load_tasks()

        # Truncate text if too long (mantendo início e fim do documento)
        max_length = 8000  # Ajuste este valor conforme necessário
        if len(text) > max_length:
            half = max_length // 2
            text = text[:half] + "\n...[TEXTO TRUNCADO]...\n" + text[-half:]
            if self.verbose:
                rprint("[yellow]Text truncated for processing[/yellow]")

        task = Task(
            description=tasks_config["metadata_extraction"]["description"],
            expected_output=tasks_config["metadata_extraction"]["expected_output"],
            agent=self.agents["metadata_agent"],
        )

        crew = Crew(
            agents=[self.agents["metadata_agent"]],
            tasks=[task],
            verbose=True,
            process=Process.sequential,  # Garantir processamento sequencial
        )

        if self.verbose:
            rprint("[green]Starting metadata extraction crew...[/green]")

        result = crew.kickoff()

        try:
            parsed_result = json.loads(result)
            if self.verbose:
                rprint("[green]Metadata extracted successfully[/green]")
            return parsed_result
        except json.JSONDecodeError as e:
            if self.verbose:
                rprint(f"[red]Error parsing metadata: {str(e)}[/red]")
            return {"error": "Failed to parse metadata"}

    def generate_summary(self, text: str, summary_type: str) -> str:
        """Generate a summary of the specified type."""
        if self.verbose:
            rprint(f"[yellow]Starting {summary_type} summary generation...[/yellow]")

        tasks_config = self._load_tasks()

        # Truncate text if too long
        max_length = 12000  # Ajuste este valor conforme necessário
        if len(text) > max_length:
            half = max_length // 2
            text = text[:half] + "\n...[TEXTO TRUNCADO]...\n" + text[-half:]
            if self.verbose:
                rprint("[yellow]Text truncated for summary generation[/yellow]")

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
            expected_output=task_config["expected_output"],
            agent=agent,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True,
            process=Process.sequential,
        )

        if self.verbose:
            rprint(f"[green]Starting {summary_type} summary generation crew...[/green]")

        result = crew.kickoff()

        if self.verbose:
            rprint(
                f"[green]{summary_type.capitalize()} summary generated successfully[/green]"
            )

        return result

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
