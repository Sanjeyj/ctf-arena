"""
AutonomousAgentService - Phase 26 Autonomous Cyber Enterprise.
Schedules, executes, and monitors autonomous software agents.
"""
from app.extensions import db, utcnow
from app.models.autonomous_agent import AutonomousAgent
from app.models.agent_task import AgentTask

class AutonomousAgentService:
    @staticmethod
    def schedule(agent_id: int, task_type: str, priority: str, organization_id: int) -> AgentTask:
        """Schedule a new task for an autonomous agent."""
        task = AgentTask(
            agent_id=agent_id,
            task_type=task_type,
            priority=priority,
            status='pending',
            organization_id=organization_id
        )
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def execute(task_id: int) -> AgentTask:
        """Simulate agent execution of a task."""
        task = AgentTask.query.get(task_id)
        if not task:
            return None

        task.status = 'running'
        db.session.commit()

        # Update last execution time on agent
        agent = task.agent
        if agent:
            agent.status = 'running'
            agent.last_execution = utcnow()
            db.session.commit()

        # Simulate work: write result depending on task type
        task.result = f"Successfully executed autonomous task {task.task_type} with priority {task.priority}."
        task.status = 'completed'
        
        if agent:
            agent.status = 'idle'
            
        db.session.commit()
        return task

    @staticmethod
    def monitor(agent_id: int) -> dict:
        """Monitor agent performance, tasks status, and health."""
        agent = AutonomousAgent.query.get(agent_id)
        if not agent:
            return {'error': f"Agent {agent_id} not found"}

        tasks_query = AgentTask.query.filter_by(agent_id=agent_id)
        total_tasks = tasks_query.count()
        completed_tasks = tasks_query.filter_by(status='completed').count()
        failed_tasks = tasks_query.filter_by(status='failed').count()

        success_rate = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 100.0

        return {
            'agent_id': agent.id,
            'name': agent.name,
            'role': agent.role,
            'status': agent.status,
            'total_tasks': total_tasks,
            'success_rate_pct': round(success_rate, 1),
            'failed_tasks': failed_tasks
        }
