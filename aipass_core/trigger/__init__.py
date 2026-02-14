"""
Trigger - Event Bus for AIPass

Usage from other branches:
    from trigger import trigger

    trigger.fire('event_name', data='value')
    trigger.on('event_name', handler_function)
    trigger.off('event_name', handler_function)
    trigger.status()
"""

from .apps.modules.core import trigger

__all__ = ['trigger']
