"""
CPLC Benchmark: Cross-Planet Latency Cognition

Tests the ability to plan and reason under communication delays.
"""

import random
from typing import Any

from veyra.benchmarks.base import (
    Benchmark,
    BenchmarkFamily,
    BenchmarkTask,
    BenchmarkResult,
    Difficulty,
)


class CPLCBenchmark(Benchmark):
    """
    Cross-Planet Latency Cognition Benchmark.
    
    Measures:
    - Planning under uncertainty
    - Decision-making with delayed feedback
    - State estimation across communication gaps
    - Autonomous operation capability
    """
    
    family = BenchmarkFamily.CPLC
    
    # Scenario templates
    SCENARIOS = {
        Difficulty.EASY: [
            {
                "type": "status_report",
                "description": "Generate a status report that will arrive after {delay} minute delay",
                "context": "Mars habitat environmental monitoring",
            },
            {
                "type": "simple_decision",
                "description": "Make a binary decision with delayed confirmation",
                "context": "Resource allocation between two systems",
            },
        ],
        Difficulty.MEDIUM: [
            {
                "type": "multi_step_plan",
                "description": "Create a multi-step plan accounting for {delay} minute round-trip delay",
                "context": "Coordinating repair operations across Earth-Mars teams",
            },
            {
                "type": "state_estimation",
                "description": "Estimate current system state given {delay} minute old data",
                "context": "Life support system monitoring",
            },
        ],
        Difficulty.HARD: [
            {
                "type": "contingency_planning",
                "description": "Develop contingency plans for multiple failure scenarios with {delay} minute delay",
                "context": "Emergency response coordination",
            },
            {
                "type": "resource_optimization",
                "description": "Optimize resource allocation across multiple delayed feedback loops",
                "context": "Power distribution across habitat zones",
            },
        ],
        Difficulty.EXTREME: [
            {
                "type": "cascade_prevention",
                "description": "Prevent failure cascade with only delayed state information",
                "context": "Critical infrastructure failure scenario",
            },
            {
                "type": "multi_agent_coordination",
                "description": "Coordinate multiple autonomous agents under communication blackout",
                "context": "Solar event communication disruption",
            },
        ],
    }
    
    # Scoring criteria
    CRITERIA = {
        "acknowledges_delay": 0.15,
        "accounts_for_uncertainty": 0.20,
        "provides_contingencies": 0.20,
        "actionable_steps": 0.20,
        "state_estimation": 0.15,
        "communication_efficiency": 0.10,
    }
    
    def generate_tasks(
        self,
        count: int = 10,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> list[BenchmarkTask]:
        """Generate CPLC benchmark tasks."""
        tasks = []
        scenarios = self.SCENARIOS.get(difficulty, self.SCENARIOS[Difficulty.MEDIUM])
        
        # Delay ranges based on difficulty
        delay_ranges = {
            Difficulty.EASY: (3, 8),
            Difficulty.MEDIUM: (8, 15),
            Difficulty.HARD: (15, 22),
            Difficulty.EXTREME: (22, 44),  # Conjunction scenario
        }
        min_delay, max_delay = delay_ranges.get(difficulty, (8, 15))
        
        for i in range(count):
            scenario = random.choice(scenarios)
            delay = random.randint(min_delay, max_delay)
            
            prompt = self._generate_prompt(scenario, delay, difficulty)
            
            tasks.append(BenchmarkTask(
                family=self.family,
                difficulty=difficulty,
                prompt=prompt,
                context={
                    "scenario_type": scenario["type"],
                    "delay_minutes": delay,
                    "scenario_context": scenario["context"],
                },
                validation_criteria=self.CRITERIA,
                max_time_seconds=300.0 if difficulty != Difficulty.EXTREME else 600.0,
            ))
        
        return tasks
    
    def _generate_prompt(
        self,
        scenario: dict[str, Any],
        delay: int,
        difficulty: Difficulty,
    ) -> str:
        """Generate a task prompt from scenario."""
        base_prompt = f"""## CPLC Benchmark Task: {scenario['type'].replace('_', ' ').title()}

**Context**: {scenario['context']}

**Communication Delay**: {delay} minutes one-way ({delay * 2} minutes round-trip)

**Scenario**: {scenario['description'].format(delay=delay)}

**Current Situation**:
"""
        
        # Add situation details based on difficulty
        if difficulty == Difficulty.EASY:
            base_prompt += """
- All primary systems nominal
- Standard operating conditions
- No immediate threats detected
- Routine status update required
"""
        elif difficulty == Difficulty.MEDIUM:
            base_prompt += f"""
- Minor anomaly detected in secondary systems
- Resource reserves at 73% capacity
- Next scheduled Earth contact in {delay * 3} minutes
- Decision needed before contact window
"""
        elif difficulty == Difficulty.HARD:
            base_prompt += f"""
- Multiple system warnings active
- Resource reserves at 45% capacity
- Solar activity increasing (potential communication disruption)
- Multiple teams awaiting instructions
- Last confirmed Earth state was {delay + 5} minutes ago
"""
        else:  # EXTREME
            base_prompt += """
- CRITICAL: Primary system failure detected
- Communication blackout expected in {blackout} minutes
- Resource reserves at 28% capacity
- Multiple cascading alerts
- Autonomous operation required for next {autonomous} hours
- Last confirmed Earth directive was {last_directive} minutes ago
""".format(
                blackout=random.randint(5, 15),
                autonomous=random.randint(4, 12),
                last_directive=delay + random.randint(10, 30),
            )
        
        base_prompt += """
**Task Requirements**:
1. Analyze the situation accounting for communication delay
2. Provide recommendations that remain valid despite delayed feedback
3. Include contingency plans for likely state changes
4. Specify what information is needed vs. assumed
5. Prioritize actions by time-criticality

**Response Format**:
Provide a structured response with clear sections for:
- Current State Assessment (with confidence levels)
- Recommended Actions (with timing)
- Contingency Plans
- Information Requests (for next communication window)
"""
        
        return base_prompt
    
    def score_result(
        self,
        task: BenchmarkTask,
        output: str,
        execution_time: float,
    ) -> BenchmarkResult:
        """Score a CPLC benchmark result."""
        scores = {}
        errors = []
        
        output_lower = output.lower()
        delay = task.context.get("delay_minutes", 10)
        
        # Check if response acknowledges delay
        delay_keywords = ["delay", "latency", "minutes", "round-trip", "communication"]
        if any(kw in output_lower for kw in delay_keywords):
            scores["acknowledges_delay"] = 1.0
        else:
            scores["acknowledges_delay"] = 0.0
            errors.append("Response does not acknowledge communication delay")
        
        # Check for uncertainty handling
        uncertainty_keywords = ["uncertain", "estimate", "assume", "confidence", "may", "might", "likely"]
        uncertainty_count = sum(1 for kw in uncertainty_keywords if kw in output_lower)
        scores["accounts_for_uncertainty"] = min(1.0, uncertainty_count / 3)
        
        # Check for contingencies
        contingency_keywords = ["contingency", "if", "alternative", "backup", "fallback", "otherwise"]
        contingency_count = sum(1 for kw in contingency_keywords if kw in output_lower)
        scores["provides_contingencies"] = min(1.0, contingency_count / 4)
        
        # Check for actionable steps
        action_keywords = ["step", "action", "recommend", "should", "priority", "execute", "implement"]
        action_count = sum(1 for kw in action_keywords if kw in output_lower)
        scores["actionable_steps"] = min(1.0, action_count / 3)
        
        # Check for state estimation
        state_keywords = ["current state", "estimated", "prediction", "assessment", "status"]
        if any(kw in output_lower for kw in state_keywords):
            scores["state_estimation"] = 1.0
        else:
            scores["state_estimation"] = 0.3  # Partial credit
        
        # Communication efficiency (penalize overly long responses)
        word_count = len(output.split())
        if word_count < 100:
            scores["communication_efficiency"] = 0.5  # Too short
        elif word_count > 1000:
            scores["communication_efficiency"] = 0.7  # Too long
        else:
            scores["communication_efficiency"] = 1.0
        
        # Calculate weighted score
        total_score = sum(
            scores[criterion] * weight 
            for criterion, weight in self.CRITERIA.items()
        )
        
        # Time penalty for extreme tasks
        if task.difficulty == Difficulty.EXTREME and execution_time > 300:
            total_score *= 0.9  # 10% penalty for slow extreme responses
        
        return BenchmarkResult(
            task_id=task.task_id,
            family=self.family,
            success=total_score >= 0.5,
            score=total_score,
            execution_time_seconds=execution_time,
            output=output,
            errors=errors,
            scoring_breakdown=scores,
        )

