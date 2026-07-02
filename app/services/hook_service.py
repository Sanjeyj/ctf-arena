import logging

logger = logging.getLogger(__name__)

class HookService:
    _hooks = {}

    @classmethod
    def register_hook(cls, hook_name, callback):
        """Register a callback function to a hook lifecycle checkpoint."""
        if hook_name not in cls._hooks:
            cls._hooks[hook_name] = []
        if callback not in cls._hooks[hook_name]:
            cls._hooks[hook_name].append(callback)
            logger.info(f"[HookService] Registered callback '{callback.__name__}' for hook '{hook_name}'")

    @classmethod
    def trigger_hook(cls, hook_name, *args, **kwargs):
        """Invoke all callbacks registered under the hook name, gathering their outputs."""
        results = []
        if hook_name in cls._hooks:
            for callback in cls._hooks[hook_name]:
                try:
                    res = callback(*args, **kwargs)
                    results.append(res)
                except Exception as e:
                    logger.error(f"[HookService] Error in hook '{hook_name}' callback '{callback.__name__}': {str(e)}", exc_info=True)
        return results

    @classmethod
    def remove_hook(cls, hook_name, callback):
        """Remove a previously registered callback from a hook list."""
        if hook_name in cls._hooks and callback in cls._hooks[hook_name]:
            cls._hooks[hook_name].remove(callback)
            logger.info(f"[HookService] Removed callback '{callback.__name__}' from hook '{hook_name}'")

    @classmethod
    def clear_all(cls):
        """Reset all hook registrations (mainly for clean test environments)."""
        cls._hooks.clear()
