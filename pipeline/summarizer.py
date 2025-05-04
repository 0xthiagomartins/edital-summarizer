from crewai import Agent, Task, Crew
from typing import Dict, List
import json
import os

class DocumentSummarizer:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv('CREWAI_API_KEY')
        if not api_key:
            raise ValueError("CrewAI API key is required. Set it in CREWAI_API_KEY environment variable.")
        
        self.metadata_agent = Agent(
            role='Metadata Extractor',
            goal='Extract structured metadata from bidding documents',
            backstory="""You are an expert in analyzing bidding documents and extracting key information.
            Your task is to identify and extract metadata such as title, organization, dates, and object.""",
            verbose=True
        )
        
        self.executive_summary_agent = Agent(
            role='Executive Summary Generator',
            goal='Generate concise executive summaries of bidding documents',
            backstory="""You are skilled at creating clear, concise executive summaries that highlight
            the most important aspects of bidding documents for decision-makers.""",
            verbose=True
        )
        
        self.technical_summary_agent = Agent(
            role='Technical Summary Generator',
            goal='Generate detailed technical summaries of bidding documents',
            backstory="""You are an expert in technical documentation and can create detailed summaries
            that focus on technical specifications, requirements, and procedures.""",
            verbose=True
        )

    def extract_metadata(self, text: str) -> Dict:
        """Extract metadata from document text."""
        task = Task(
            description=f"""Extract the following metadata from the document text:
            - Title
            - Organization/Entity
            - Publication Date
            - Deadline Date
            - Object/Subject
            - Reference Number
            - Estimated Value
            - Contact Information
            
            Return the data in JSON format.""",
            agent=self.metadata_agent
        )
        
        crew = Crew(
            agents=[self.metadata_agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "Failed to parse metadata"}

    def generate_summary(self, text: str, summary_type: str) -> str:
        """Generate a summary of the specified type."""
        if summary_type == "executivo":
            agent = self.executive_summary_agent
            prompt = "Generate a concise executive summary focusing on key points and decisions needed."
        elif summary_type == "técnico":
            agent = self.technical_summary_agent
            prompt = "Generate a detailed technical summary focusing on specifications and requirements."
        else:
            raise ValueError(f"Unknown summary type: {summary_type}")

        task = Task(
            description=f"{prompt}\n\nDocument text:\n{text}",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        return crew.kickoff()

    def process_document(self, text: str, summary_types: List[str] = None) -> Dict:
        """Process a document and generate all requested summaries."""
        if summary_types is None:
            summary_types = ["executivo", "técnico"]
            
        result = {
            "metadata": self.extract_metadata(text),
            "summaries": {}
        }
        
        for summary_type in summary_types:
            result["summaries"][summary_type] = self.generate_summary(text, summary_type)
            
        return result 