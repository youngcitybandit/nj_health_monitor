"""
Task scheduler for running daily monitoring checks.
"""

import schedule
import time
import logging
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Handles scheduling of monitoring tasks."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.running = False
        self.scheduler_thread = None
    
    def schedule_daily_task(self, task_function, time_str="09:00"):
        """
        Schedule a task to run daily at a specific time.
        
        Args:
            task_function: The function to run
            time_str: Time in HH:MM format (24-hour)
        """
        try:
            schedule.every().day.at(time_str).do(self._run_task_with_logging, task_function)
            logger.info(f"Daily task scheduled for {time_str}")
        except Exception as e:
            logger.error(f"Error scheduling daily task: {str(e)}")
            raise
    
    def schedule_multiple_daily_tasks(self, task_function, time_strings):
        """
        Schedule a task to run multiple times daily at specified times.
        
        Args:
            task_function: The function to run
            time_strings: List of time strings in HH:MM format (24-hour)
        """
        try:
            for time_str in time_strings:
                schedule.every().day.at(time_str).do(self._run_task_with_logging, task_function)
                logger.info(f"Daily task scheduled for {time_str}")
            logger.info(f"Scheduled {len(time_strings)} daily checks")
        except Exception as e:
            logger.error(f"Error scheduling multiple daily tasks: {str(e)}")
            raise
    
    def schedule_hourly_task(self, task_function):
        """Schedule a task to run every hour."""
        try:
            schedule.every().hour.do(self._run_task_with_logging, task_function)
            logger.info("Hourly task scheduled")
        except Exception as e:
            logger.error(f"Error scheduling hourly task: {str(e)}")
            raise
    
    def schedule_custom_interval(self, task_function, interval_minutes=60):
        """
        Schedule a task to run at custom intervals.
        
        Args:
            task_function: The function to run
            interval_minutes: Interval in minutes
        """
        try:
            schedule.every(interval_minutes).minutes.do(self._run_task_with_logging, task_function)
            logger.info(f"Task scheduled every {interval_minutes} minutes")
        except Exception as e:
            logger.error(f"Error scheduling custom interval task: {str(e)}")
            raise
    
    def _run_task_with_logging(self, task_function):
        """Run a task with proper logging and error handling."""
        start_time = datetime.now()
        logger.info(f"Starting scheduled task: {task_function.__name__}")
        
        try:
            task_function()
            duration = datetime.now() - start_time
            logger.info(f"Task completed successfully in {duration.total_seconds():.2f} seconds")
        except Exception as e:
            duration = datetime.now() - start_time
            logger.error(f"Task failed after {duration.total_seconds():.2f} seconds: {str(e)}")
    
    def run(self):
        """Start the scheduler in a separate thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Continue running even if there's an error
    
    def get_next_run_times(self):
        """Get the next run times for all scheduled jobs."""
        jobs = schedule.get_jobs()
        next_runs = []
        
        for job in jobs:
            next_run = job.next_run
            if next_run:
                next_runs.append({
                    'job': str(job.job_func),
                    'next_run': next_run.isoformat(),
                    'interval': str(job.interval) if hasattr(job, 'interval') else 'daily'
                })
        
        return next_runs
    
    def clear_all_jobs(self):
        """Clear all scheduled jobs."""
        schedule.clear()
        logger.info("All scheduled jobs cleared")
    
    def is_running(self):
        """Check if the scheduler is running."""
        return self.running
    
    def get_job_count(self):
        """Get the number of scheduled jobs."""
        return len(schedule.get_jobs())
