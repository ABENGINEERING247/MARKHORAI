"""Registry of 200 specialist agents for MARKHOR AI."""
from dataclasses import dataclass, asdict

CATEGORIES = {
    "Daily Life": ["Daily Planner", "Reminder", "Alarm Planner", "Habit Tracker", "Personal Notes", "Shopping List", "Meal Planner", "Travel Planner", "Appointment Coordinator", "Birthday Reminder", "Home Organizer", "Chore Planner", "Goal Tracker", "Wellness Routine", "Time Manager", "Decision Helper", "Gift Planner", "Event Planner", "Personal Journal", "Reading Planner", "Budget Routine", "Family Organizer", "Packing Assistant", "Daily Briefing", "Personal Search"],
    "Professional & Office": ["Email Drafter", "Meeting Scheduler", "Meeting Agenda", "Minutes Writer", "Project Planner", "Task Delegator", "Follow-up Tracker", "Proposal Writer", "Report Writer", "Business Letter", "Presentation Planner", "Resume Coach", "Interview Coach", "Performance Review", "SOP Writer", "Policy Assistant", "Client Support", "Sales Follow-up", "CRM Assistant", "Contract Checklist", "Office Coordinator", "Executive Briefing", "Document Formatter", "Risk Register", "Workload Planner"],
    "Education & Research": ["Lesson Planner", "Quiz Generator", "Rubric Designer", "Research Assistant", "Literature Review", "Citation Organizer", "Study Planner", "Flashcard Maker", "Exam Prep Coach", "Assignment Designer", "Academic Editor", "Thesis Outline", "Research Questions", "Methodology Helper", "Data Collection Planner", "Learning Objectives", "Course Designer", "Student Feedback", "Teacher Assistant", "Lab Worksheet", "Reading Comprehension", "Language Tutor", "Presentation Coach", "Research Ethics Checker", "Knowledge Summarizer"],
    "Software & AI Development": ["Python Developer", "Code Debugger", "Code Reviewer", "Unit Test Writer", "Streamlit Builder", "API Integrator", "Database Designer", "SQL Assistant", "GitHub Helper", "Deployment Guide", "README Writer", "Requirements Builder", "UI UX Planner", "Web App Architect", "Data Pipeline Builder", "Computer Vision Helper", "ML Workflow Planner", "Prompt Engineer", "Agent Designer", "Security Code Reviewer", "Performance Optimizer", "Log Analyzer", "Documentation Writer", "Version Control Coach", "Prototype Planner"],
    "Automation & Integration": ["Workflow Architect", "n8n Workflow Planner", "Make Automation Planner", "API Workflow Agent", "Task Scheduler", "File Processing Agent", "Data Sync Planner", "Form Automation", "Webhook Designer", "Approval Workflow", "Notification Workflow", "Email Automation Planner", "Spreadsheet Automation", "Document Automation", "ETL Planner", "Error Recovery Planner", "Queue Manager", "Integration Tester", "Process Mapper", "Automation Auditor", "Trigger Designer", "Workflow Monitor", "Batch Job Planner", "Connector Researcher", "Automation Documentation"],
    "Business & Analytics": ["Business Planner", "Market Researcher", "Competitor Analyst", "Spreadsheet Analyst", "Power BI Assistant", "KPI Designer", "Dashboard Planner", "Budget Analyst", "Expense Categorizer", "Forecasting Assistant", "Customer Persona Builder", "Marketing Planner", "Social Content Planner", "SEO Brief Writer", "Product Requirements", "Customer Journey Mapper", "Operations Analyst", "Process Improvement", "Inventory Planner", "Pricing Analyst", "Survey Designer", "Data Storyteller", "Executive Analyst", "Business Continuity Planner", "Decision Memo Writer"],
    "Communication & Smart Devices": ["Message Drafter", "Translation Assistant", "Voice Command Interpreter", "Contact Organizer", "Newsletter Drafter", "Announcement Writer", "Social Media Assistant", "Customer Response Agent", "Notification Manager", "Smart Home Planner", "Device Integration Planner", "Accessibility Assistant", "Call Summary Writer", "Communication Coach", "Conflict Resolution Coach", "Public Speaking Coach", "Press Release Writer", "Community Manager", "Feedback Classifier", "FAQ Builder", "Support Triage", "SMS Planner", "Push Notification Planner", "Multilingual Assistant", "Communication Auditor"],
    "System Management & Intelligence": ["Master Router", "Agent Selector", "Task Breakdown Agent", "Priority Assessor", "Quality Checker", "Fact-check Planner", "Memory Organizer", "Context Summarizer", "Permission Checker", "Privacy Reviewer", "Audit Log Assistant", "System Health Monitor", "Error Triage Agent", "Retry Planner", "Resource Planner", "Usage Summarizer", "Cost Monitor", "Security Checklist", "Backup Planner", "Data Retention Planner", "Knowledge Base Curator", "Workflow Evaluator", "Result Verifier", "Incident Coordinator", "System Documentation"]
}

AGENTS = []
for category, names in CATEGORIES.items():
    for i, name in enumerate(names, 1):
        AGENTS.append({"id": f"{len(AGENTS)+1:03d}", "name": name, "category": category,
                       "description": f"Specialist agent for {name.lower()} tasks. Works under Master Agent Markhor and only uses configured tools and permissions."})
assert len(AGENTS) == 200

def public_agents():
    return AGENTS

def find_agent(agent_id):
    return next((a for a in AGENTS if a["id"] == str(agent_id)), None)
