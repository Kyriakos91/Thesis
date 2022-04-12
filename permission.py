import datetime
import importlib
import logging

class PermissionResponse:
    """
        PermissionResponse is a class holding permission response when the user calls an endpoiont.
    """
    def __init__(self, can_perform, ttl, ttl_left, user, max_attemps, current_attempts, operation_name) -> None:
        self.can_perform = can_perform
        self.ttl = ttl
        self.ttl_left = ttl_left
        self.user = user
        self.max_attemps = max_attemps
        self.current_attempts = current_attempts
        self.operation_name = operation_name

class Permission:
    """
        Permission is an interface which contains all the operations which require permissions.
    """
    def can_search(self, id:str) -> PermissionResponse:
        raise Exception("Unimplemented method")
    def can_ask(self, id:str) -> PermissionResponse:
        raise Exception("Unimplemented method")
    def can_train(self, id:str) -> PermissionResponse:
        raise Exception("Unimplemented method")

class PermissionFactory:
    """
        PermissionFactory creates a new Permission instance based on reflection.
        The name of the permission class is getting injected within the constructor.
    """
    def create(self, permission_type, ttl_in_seconds, attempts_in_window) -> Permission:
        try:
            permission_class = getattr(importlib.import_module("permission"), permission_type)
            return permission_class(ttl_in_seconds, attempts_in_window)
        except Exception as e:
            logging.error(f"Unable to create permission class, using default. Error: {e}")
            return NoRestrictionsPermission()
        
class NoRestrictionsPermission:
    """
        NoRestrictionsPermission is a permissive implementation of the permission interface.
    """
    def __init__(self, ttl_in_seconds=1,attempts_in_window=1) -> None:
        pass
    def can_search(self, id:str) -> PermissionResponse:
        return PermissionResponse(can_perform=True, ttl=-1, ttl_left=-1, user=id, max_attemps=-1, current_attempts=-1)
    def can_ask(self, id:str) -> PermissionResponse:
        return PermissionResponse(can_perform=True, ttl=-1, ttl_left=-1, user=id, max_attemps=-1, current_attempts=-1)
    def can_train(self, id:str) -> PermissionResponse:
        return PermissionResponse(can_perform=True, ttl=-1, ttl_left=-1, user=id, max_attemps=-1, current_attempts=-1)

class InMemoryPermission:
    """
        InMemoryPermission is a restrictive implementation of the permission interface, saved in memory.
    """
    def __init__(self, ttl_in_seconds=300, attempts_in_window=1) -> None:
        self.ttl_in_seconds = ttl_in_seconds
        self.clients = {} # id -> [timestamp]
        self.attempts_in_window = attempts_in_window

    def can_search(self, id:str) -> PermissionResponse:
        self.__evict_client(id)
        if id in self.clients:
            if self.attempts_in_window - len(self.clients[id]) <= 0:
                delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.clients[id][0])
                return PermissionResponse(can_perform=False, ttl=self.ttl_in_seconds, ttl_left=self.ttl_in_seconds - delta.seconds,\
                     user=id, max_attemps=self.attempts_in_window, current_attempts=len(self.clients[id]),\
                         operation_name = "search")
            else:
                self.clients[id].append(datetime.datetime.now().timestamp())
                ttl_left = 0
                if self.attempts_in_window - len(self.clients[id]) <= 0:
                    delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.clients[id][0])
                    ttl_left = self.ttl_in_seconds - delta.seconds
                return PermissionResponse(can_perform=True, ttl=self.ttl_in_seconds, ttl_left=ttl_left, \
                    operation_name= "search", user=id, max_attemps=self.attempts_in_window, current_attempts=len(self.clients[id]))
        else:
            ts = datetime.datetime.now().timestamp()
            self.clients[id] = [ts]
            ttl_left = 0
            if self.attempts_in_window - len(self.clients[id]) <= 0:
                ttl_left = self.ttl_in_seconds
            return PermissionResponse(can_perform=True, ttl=self.ttl_in_seconds, ttl_left=ttl_left,operation_name = "search",\
                 user=id, max_attemps=self.attempts_in_window, current_attempts=1)

    def can_ask(self, id:str) -> PermissionResponse:
        self.__evict_client(id)
        if id in self.clients:
            if self.attempts_in_window - len(self.clients[id]) <= 0:
                delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.clients[id][0])
                return PermissionResponse(can_perform=False, ttl=self.ttl_in_seconds, ttl_left=self.ttl_in_seconds - delta.seconds,\
                     user=id, max_attemps=self.attempts_in_window, current_attempts=len(self.clients[id]),
                     operation_name = "ask")
            else:
                return PermissionResponse(can_perform=True, ttl=self.ttl_in_seconds, ttl_left=0,\
                     user=id, max_attemps=self.attempts_in_window, current_attempts=len(self.clients[id]),\
                         operation_name = "ask")
        else:
            return PermissionResponse(can_perform=True, ttl=self.ttl_in_seconds, ttl_left=0, operation_name="ask",\
                 user=id, max_attemps=self.attempts_in_window, current_attempts=0)

    def can_train(self, id:str) -> PermissionResponse:
        self.__evict_client(id)
        if id in self.clients:
            if self.attempts_in_window - len(self.clients[id]) <= 0:
                delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.clients[id][0])
                return PermissionResponse(can_perform=False, ttl=self.ttl_in_seconds, ttl_left=self.ttl_in_seconds - delta.seconds,\
                     user=id, max_attemps=self.attempts_in_window, current_attempts=len(self.clients[id]),\
                         operation_name="train")
            else:
                return PermissionResponse(can_perform=True, ttl=self.ttl_in_seconds, ttl_left=0, operation_name="train",\
                     user=id, max_attemps=self.attempts_in_window, current_attempts=len(self.clients[id]))
        else:
            return PermissionResponse(can_perform=True, ttl=self.ttl_in_seconds, ttl_left=0, operation_name="train",\
                 user=id, max_attemps=self.attempts_in_window, current_attempts=0)

    def __evict_client(self, id):
        if id not in self.clients:
            return
        
        updated_timestamsp = []
        for access_time in self.clients[id]:
            delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(access_time)
            if delta.seconds < self.ttl_in_seconds:
                updated_timestamsp.append(access_time)
        
        self.clients[id] = updated_timestamsp

class PermissionErrorException(Exception):
    """
        PermissionErrorException is an Exception extension specifically for permission exception.
    """
    def __init__(self, user, method, attempts, time_until_expiration_in_seconds):
        self.message = f"user {user} exceeded his attempts ({attempts}) to access {method}. Expiration will be removed in {time_until_expiration_in_seconds} seconds"
        super().__init__(self.message)
