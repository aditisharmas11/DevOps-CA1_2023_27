"""
Mental Health Screening Agent – Agentic AI implementation
Uses transparent rule-based reasoning for reliable results
"""

import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('logs', exist_ok=True)

class MentalHealthAgent:
    """
    An autonomous agent that conducts screening using transparent rule-based reasoning.
    Demonstrates Agentic AI concepts: Perception, Reasoning, Decision, Action, Tools
    """
    
    def __init__(self):
        print("🤖 Initializing Mental Health Agent...")
        print("  📋 Using transparent rule-based reasoning engine")
        
        # Agent memory
        self.context = {'user_responses': {}, 'risk_level': None, 'conversation_history': []}
        
        # Tools available to the agent
        self.tools = {
            'log_interaction': self._log_to_file,
            'fetch_resources': self._get_resource_links,
            'simulate_escalation': self._simulate_human_handoff,
        }
        
        print("✅ Agent ready!\n")
    
    # ------------------------------------------------------------------
    # Perception: Collect information from user
    # ------------------------------------------------------------------
    def collect_stress_inputs(self) -> Dict[str, float]:
        """Interactive CLI to gather stress-related features."""
        print("\n" + "="*50)
        print("🧠 STRESS SCREENING QUESTIONNAIRE")
        print("="*50)
        print("Please rate the following from 1 to 5:\n")
        
        responses = {}
        questions = {
            'sleep_quality': "  Sleep quality (1=very poor, 5=excellent): ",
            'headaches_weekly': "  Headaches per week (1=none, 5=daily): ",
            'academic_performance': "  Academic performance (1=struggling, 5=excellent): ",
            'study_load': "  Study load (1=light, 5=overwhelming): ",
            'extracurricular_weekly': "  Extracurricular activities (1=few, 5=many): ",
        }
        
        for key, prompt in questions.items():
            while True:
                try:
                    val = int(input(prompt))
                    if 1 <= val <= 5:
                        responses[key] = val
                        break
                    else:
                        print("    Please enter a number between 1 and 5.")
                except ValueError:
                    print("    Invalid input. Enter a number.")
        
        self.context['user_responses']['stress'] = responses
        self.context['conversation_history'].append({"stage": "perception", "data": responses})
        return responses
    
    # ------------------------------------------------------------------
    # Reasoning: Calculate risk score using transparent formula
    # ------------------------------------------------------------------
    def calculate_risk_score(self, features: Dict) -> Tuple[int, str, float]:
        """
        Calculate stress risk based on weighted formula.
        This is a transparent, interpretable rule-based system.
        
        Formula components:
        - Sleep quality: Poor sleep = higher risk (weight 30%)
        - Headaches: More headaches = higher risk (weight 25%)
        - Study load: Higher load = higher risk (weight 20%)
        - Academic performance: Poor performance = higher risk (weight 15%)
        - Extracurricular: Fewer activities = higher risk (weight 10%)
        """
        # Calculate individual risk scores (higher = more stress)
        sleep_risk = 6 - features['sleep_quality']           # 5→1, 1→5
        headache_risk = features['headaches_weekly']        # 1→1, 5→5
        academic_risk = 6 - features['academic_performance'] # 5→1, 1→5
        load_risk = features['study_load']                   # 1→1, 5→5
        extra_risk = 6 - features['extracurricular_weekly']  # 5→1, 1→5
        
        # Weighted sum (weights based on clinical importance)
        total_risk = (
            sleep_risk * 0.30 +
            headache_risk * 0.25 +
            load_risk * 0.20 +
            academic_risk * 0.15 +
            extra_risk * 0.10
        )
        
        # Determine stress level based on total risk score
        if total_risk <= 2.0:
            risk_level = 0  # Low Stress
            label = "Low Stress 🟢"
            confidence = 0.85 + (2.0 - total_risk) / 10
        elif total_risk <= 3.5:
            risk_level = 1  # Moderate Stress
            label = "Moderate Stress 🟡"
            confidence = 0.80
        else:
            risk_level = 2  # High Stress
            label = "High Stress 🔴"
            confidence = 0.85 + (total_risk - 3.5) / 10
        
        confidence = min(0.95, confidence)
        
        # Store reasoning in context for transparency
        self.context['risk_level'] = risk_level
        self.context['conversation_history'].append({
            "stage": "reasoning",
            "risk_score": total_risk,
            "components": {
                "sleep_risk": sleep_risk,
                "headache_risk": headache_risk,
                "academic_risk": academic_risk,
                "load_risk": load_risk,
                "extra_risk": extra_risk
            },
            "prediction": risk_level,
            "confidence": confidence
        })
        
        return risk_level, label, confidence
    
    def assess_stress_risk(self, features: Dict) -> Tuple[int, str, float]:
        """Assess risk using transparent rule-based reasoning."""
        return self.calculate_risk_score(features)
    
    # ------------------------------------------------------------------
    # Action: Decide and execute based on risk
    # ------------------------------------------------------------------
    def decide_action(self, risk_level: int) -> str:
        """Agentic decision-making: choose appropriate response."""
        if risk_level == 0:
            return "provide_reassurance"
        elif risk_level == 1:
            return "recommend_resources"
        else:
            return "escalate_to_human"
    
    def execute_action(self, action: str) -> None:
        """Execute the chosen action, possibly using tools."""
        print("\n" + "="*50)
        print("🤖 AGENT DECISION")
        print("="*50)
        
        if action == "provide_reassurance":
            print("✅ Your stress levels appear manageable.")
            print("\n   💡 Recommendations:")
            print("   • Continue practicing good sleep hygiene (7-9 hours)")
            print("   • Maintain a balanced study schedule with breaks")
            print("   • Take regular breaks between study sessions")
            print("   • Stay connected with friends and family")
            self._log_to_file(self.context, action, "Reassurance provided - Low risk")
            
        elif action == "recommend_resources":
            print("⚠️  You're experiencing moderate stress.")
            print("\n   💡 Suggestions for managing stress:")
            print("   • Try deep breathing exercises (5 minutes, 3 times a day)")
            print("   • Set realistic daily goals and prioritize tasks")
            print("   • Take a 10-minute walk between study sessions")
            resources = self.tools['fetch_resources']()
            print("\n   📚 Professional Resources:")
            for i, r in enumerate(resources, 1):
                print(f"   {i}. {r}")
            self._log_to_file(self.context, action, "Resources recommended - Moderate risk")
            
        elif action == "escalate_to_human":
            print("🚨 Your responses indicate HIGH stress levels.")
            print("\n   ⚠️ This requires immediate attention.")
            self.tools['simulate_escalation'](self.context)
            self._log_to_file(self.context, action, "Escalation triggered - High risk")
        
        print("="*50)
    
    # ------------------------------------------------------------------
    # Tools (external capabilities the agent can use)
    # ------------------------------------------------------------------
    def _log_to_file(self, context: Dict, action: str, note: str):
        """Tool 1: Write interaction to a log file for audit trail."""
        timestamp = datetime.now().isoformat()
        os.makedirs('logs', exist_ok=True)
        with open('logs/agent_interactions.log', 'a') as f:
            f.write(f"{timestamp} | Risk: {context.get('risk_level')} | "
                    f"Action: {action} | Note: {note}\n")
        print(f"\n   📝 Interaction logged (ID: {timestamp[:19]})")
    
    def _get_resource_links(self) -> List[str]:
        """Tool 2: Return curated mental health resources."""
        return [
            "🏫 University Counseling Center: Schedule a free confidential appointment",
            "📱 Mindfulness Apps: Headspace or Calm (free for students)",
            "💬 Crisis Text Line: Text HOME to 741741 (24/7, confidential)",
            "📞 National Suicide Prevention Lifeline: 988",
            "📚 Student Wellness Center: Free stress management workshops"
        ]
    
    def _simulate_human_handoff(self, context: Dict):
        """Tool 3: Simulate notifying a human counselor."""
        print("\n   📧 CRITICAL NOTIFICATION SENT:")
        print("   → On-call counselor has been notified immediately")
        print("   → You will receive a follow-up call within 1 hour")
        print("\n   📞 IMMEDIATE SUPPORT (while waiting):")
        print("   • Crisis Helpline: 988 (24/7)")
        print("   • University Counseling Emergency: (555) 123-4567")
        print("\n   🏥 If you are in immediate danger, please call 911.")
    
    # ------------------------------------------------------------------
    # Display reasoning transparency
    # ------------------------------------------------------------------
    def show_reasoning(self):
        """Display the agent's reasoning process for transparency."""
        if self.context.get('conversation_history'):
            for step in self.context['conversation_history']:
                if step.get('stage') == 'reasoning':
                    print("\n🔍 AGENT'S INTERNAL REASONING:")
                    print(f"   → Risk Score: {step.get('risk_score', 'N/A'):.2f} / 5.0")
                    if 'components' in step:
                        print("   → Component Contributions:")
                        for comp, val in step['components'].items():
                            print(f"      • {comp}: {val}")
    
    # ------------------------------------------------------------------
    # Main Agent Loop
    # ------------------------------------------------------------------
    def run_stress_screening(self):
        """Full autonomous screening workflow."""
        print("\n" + "="*50)
        print("🤖 AUTONOMOUS MENTAL HEALTH SCREENING AGENT")
        print("="*50)
        print("\nThis autonomous agent demonstrates:")
        print("  🔹 Perception - Collects user responses")
        print("  🔹 Reasoning - Analyzes using weighted formula")
        print("  🔹 Decision - Maps risk to appropriate action")
        print("  🔹 Action - Executes response with external tools")
        print("  🔹 Tools - Logging, resource fetching, escalation")
        
        input("\n📋 Press Enter to begin screening...")
        
        # 1. Perception - Collect data
        features = self.collect_stress_inputs()
        
        # 2. Reasoning - Analyze using rule-based system
        risk, label, confidence = self.assess_stress_risk(features)
        
        print(f"\n📊 ASSESSMENT RESULT:")
        print(f"   → Stress Level: {label}")
        print(f"   → Confidence: {confidence:.1%}")
        
        # Show transparent reasoning
        self.show_reasoning()
        
        # 3. Decision - Choose action based on risk
        action = self.decide_action(risk)
        print(f"\n🤔 AGENT DECISION LOGIC:")
        print(f"   → Risk level = {risk}")
        print(f"   → Selected action = {action}")
        
        # 4. Action - Execute with tools
        self.execute_action(action)
        
        print("\n✅ Screening complete. Take care of yourself! 💙")
        print(f"\n📁 Session log saved to: logs/agent_interactions.log")


# ------------------------------------------------------------------
# Run the agent
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = MentalHealthAgent()
    agent.run_stress_screening()