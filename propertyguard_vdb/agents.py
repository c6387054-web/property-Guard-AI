import os
from crewai import Agent, Crew, Process, Task
from langchain_google_genai import ChatGoogleGenerativeAI
from propertyguard_vdb.schemas import VerificationResponse

def build_verification_crew(listing_data: dict, extracted_doc_text: str, duplicate_match_info: dict) -> Crew:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.environ.get("GEMINI_API_KEY"),
        temperature=0.1,
    )

    doc_agent = Agent(
        role="Document Analysis Specialist",
        goal="Extract property area, registered owner name, and deed references from document text.",
        backstory="Forensic land registry auditor proficient in deed analysis.",
        llm=llm,
        verbose=False
    )

    duplicate_agent = Agent(
        role="Duplicate Detection Auditor",
        goal="Determine if the listing collides with existing vector records.",
        backstory="Database auditor specialized in catching multi-posted fraudulent real estate ads.",
        llm=llm,
        verbose=False
    )

    claim_agent = Agent(
        role="Claim Verification Specialist",
        goal="Compare user declared claims against document findings.",
        backstory="Cross-examiner detecting area discrepancies and mismatched identities.",
        llm=llm,
        verbose=False
    )

    risk_agent = Agent(
        role="Risk Analysis Specialist",
        goal="Compute risk score (0-100) and compile issues with severity ratings.",
        backstory="Real estate fraud risk evaluator.",
        llm=llm,
        verbose=False
    )

    coordinator_agent = Agent(
        role="PropertyGuard Coordinator",
        goal="Assemble all outputs into the final VerificationResponse structure.",
        backstory="Lead verification coordinator ensuring compliance with output schema.",
        llm=llm,
        verbose=False
    )

    t1 = Task(
        description=f"Extract area number, measurement unit, and owner name from this text:\n{extracted_doc_text}",
        expected_output="Document facts containing exact numerical area and owner names.",
        agent=doc_agent
    )

    t2 = Task(
        description=f"Evaluate duplicate match information: {duplicate_match_info}",
        expected_output="Risk tone and duplicate findings summary.",
        agent=duplicate_agent
    )

    t3 = Task(
        description=f"Compare listing: Title='{listing_data['title']}', Owner='{listing_data['owner']}', Area={listing_data['area']} {listing_data['unit']} with extracted facts.",
        expected_output="Reconciliation note between declared and document facts.",
        agent=claim_agent
    )

    t4 = Task(
        description="Compute final risk score (0 to 100) and compile list of issues with severity ('High', 'Medium', or 'Low').",
        expected_output="Calculated risk score and categorized issues.",
        agent=risk_agent
    )

    t5 = Task(
        description="Format all findings into the strict VerificationResponse JSON schema.",
        expected_output="Structured JSON matching VerificationResponse model.",
        agent=coordinator_agent,
        output_pydantic=VerificationResponse
    )

    return Crew(
        agents=[doc_agent, duplicate_agent, claim_agent, risk_agent, coordinator_agent],
        tasks=[t1, t2, t3, t4, t5],
        process=Process.sequential,
        verbose=False
    )