#!/usr/bin/env python3
"""Observer Pattern Implementation for Resource Monitoring.

Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Any, List, Set
from weakref import WeakSet


class Observer(ABC):
    """Abstract base class for observers."""
    
    @abstractmethod
    def update(self, subject: 'Subject', event_type: str, data: Any) -> None:
        """Handle updates from subject.
        
        Args:
            subject: The subject that triggered the update
            event_type: Type of event that occurred
            data: Event data
        """
        pass


class Subject:
    """Subject class that notifies observers of changes."""
    
    def __init__(self):
        self._observers: WeakSet[Observer] = WeakSet()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def attach(self, observer: Observer) -> None:
        """Attach an observer.
        
        Args:
            observer: Observer to attach
        """
        with self._lock:
            self._observers.add(observer)
            self._logger.debug(f"Observer {observer.__class__.__name__} attached")
    
    def detach(self, observer: Observer) -> None:
        """Detach an observer.
        
        Args:
            observer: Observer to detach
        """
        with self._lock:
            self._observers.discard(observer)
            self._logger.debug(f"Observer {observer.__class__.__name__} detached")
    
    def notify(self, event_type: str, data: Any = None) -> None:
        """Notify all observers of an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        with self._lock:
            observers = list(self._observers)  # Create snapshot to avoid iteration issues
        
        for observer in observers:
            try:
                observer.update(self, event_type, data)
            except Exception as e:
                self._logger.error(f"Error notifying observer {observer.__class__.__name__}: {e}")