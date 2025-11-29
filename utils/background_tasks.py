"""Background task management for long-running operations"""
import threading
import queue
from typing import Callable, Any, Optional
import streamlit as st

class BackgroundTaskManager:
    """Manages background tasks for Streamlit"""
    
    def __init__(self):
        # Store references to regular dictionaries so background threads can
        # safely update them even if Streamlit resets session_state
        self.background_tasks = st.session_state.setdefault('background_tasks', {})
        self.task_results = st.session_state.setdefault('task_results', {})
        self.task_errors = st.session_state.setdefault('task_errors', {})
    
    def run_task(self, task_id: str, func: Callable, *args, **kwargs):
        """
        Run a function in the background
        
        Args:
            task_id: Unique identifier for the task
            func: Function to run
            *args, **kwargs: Arguments to pass to the function
        """
        if task_id in self.background_tasks:
            # Task already running
            return
        
        # Mark task as running
        self.background_tasks[task_id] = True
        self.task_results[task_id] = None
        self.task_errors[task_id] = None
        
        def task_wrapper():
            try:
                result = func(*args, **kwargs)
                self.task_results[task_id] = result
            except Exception as e:
                self.task_errors[task_id] = str(e)
            finally:
                self.background_tasks[task_id] = False
        
        thread = threading.Thread(target=task_wrapper, daemon=True)
        thread.start()
    
    def is_running(self, task_id: str) -> bool:
        """Check if a task is currently running"""
        return self.background_tasks.get(task_id, False)
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task"""
        return self.task_results.get(task_id)
    
    def get_error(self, task_id: str) -> Optional[str]:
        """Get the error of a failed task"""
        return self.task_errors.get(task_id)
    
    def is_complete(self, task_id: str) -> bool:
        """Check if a task is complete (successfully or with error)"""
        if task_id not in self.background_tasks:
            return False
        return not self.background_tasks[task_id]
    
    def clear_task(self, task_id: str):
        """Clear a task from state"""
        if task_id in self.background_tasks:
            del self.background_tasks[task_id]
        if task_id in self.task_results:
            del self.task_results[task_id]
        if task_id in self.task_errors:
            del self.task_errors[task_id]

