# -*- coding: utf-8 -*-
"""Resources definition and implementation, including quests & materials / areas and background knowledge."""

import json
import time
from typing import Any, Dict, Tuple
import uuid
from loguru import logger

from agentscope.agents import AgentBase
from agentscope.message import Msg


class Error(str):
    def __init__(self, msg="") -> None:
        self.msg = msg
        
    def __str__(self) -> str:
        return self.msg


class ObjectMeta(dict):
    
    def __init__(self, 
                 name="",
                 type="basic",
                 description="",
                 possesser_id="",
                 type_id="",
                 **kwargs) -> None:
        self.name = name
        self.object_id = f"{self.name}_{uuid.uuid4().hex}"
        self.type_id = type_id
        self.description = description
        self.possesser_id = possesser_id
        self.type = type
        
        self.update(kwargs)
        
    def __getattr__(self, key: Any) -> Any:
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e

    def __setattr__(self, key: Any, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: Any) -> None:
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e
        
    def __eq__(self, another: Any) -> bool:
        return isinstance(another, self.__class__) and self.type_id == another.type_id
    
    def __hash__(self) -> int:
        return hash(self.type_id)
    
    def __str__(self) -> str:
        return f"{self.name}:({self.type_id})"


class Lumber(ObjectMeta):
    def __init__(self, 
                 possesser_id="",) -> None:
        super().__init__(name="lumber",
                         type="material",
                         description="A piece of wood.",
                         type_id="lumber-0",
                         possesser_id=possesser_id)
    

class QuestMeta(dict):
    def __init__(self, 
                 name="basic_quest",
                 description="It's a quest base",
                 hint="You need to do something.",
                 unfinished_msg="The quest is not finished yet. Current status: {current_status}",
                 finished_msg="Congrats! You've finished the quest.",
                 materials_requirement: Dict[ObjectMeta, int] = {},
                 **kwargs) -> None:
        self.name = name
        self.quest_id = f"{self.name}_{uuid.uuid4().hex}"
        self.description = description
        self.hint = hint
        self.unfinished_msg = unfinished_msg
        self.finished_msg = finished_msg
        self.materials_requirement = materials_requirement
        
        self.update(kwargs)
        
    def __getattr__(self, key: Any) -> Any:
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e

    def __setattr__(self, key: Any, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: Any) -> None:
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e


class Quest(AgentBase):
    '''
    A Quest is a specific goal or objective, assigned by player to an agent, that requires submitting certain number and type of materials.
    '''
    def __init__(self, 
                 quest_meta: QuestMeta=QuestMeta()) -> None:
        self.quest_meta = quest_meta
        self.current_status: Dict = {} # {material: amount}
        
        super().__init__(name=quest_meta, use_memory=False)
    
    def reply(self, x: dict = None) -> dict:
        '''
        In this method, `x` is the submission of materials required and its possessor's id, which is the agent id.
        
        Reply message varies by the number of materials.
        
        Args:
            x (`dict`):
                The submission of materials and its possessor's id. 
        
        Returns:
            The quest's finish status and message, including status and hints.
        '''
        err = self._validate(x)
        if err != None:
            logger.error(f"Invalid submission: {err}")
            return {
                "message": f"Invalid submission: {err}",
                "finished": False,
                "hint": self.quest_meta.hint,
            }
            
        material_submission: Dict = x['content']
        
        for material, amount in material_submission.items():
            if material in self.quest_meta.materials_requirement:
                self.current_status[material] = self.current_status.get(material, 0) + amount
        
        if self._is_finished():
            content = {
                "message": self.quest_meta.finished_msg,
                "finished": True,
            }
        else:
            content = {
                "message": self.quest_meta.unfinished_msg.format_map({
                   "current_status": self._current_status_str(),
                }),
                "finished": False,
                "hint": self.quest_meta.hint,
            }
        
        return Msg(name=self.name, content=content, role="assistant")
        
    def _validate(self, x: dict) -> Error:
        # TODO: validate if x is compatible
        if not isinstance(x, dict):
            return Error("x must be a dict")
        
        if "content" not in x:
            return Error("x must contain a 'content' field")
        
        if not isinstance(x['content'], dict):
            return Error("x['content'] must be a dict")
            
        return None
    
    def _current_status_str(self) -> str:
        '''
        Return material and amount in string format
        '''
        res = {}
        for material, amount in self.current_status.items():
            res[str(material)] = amount
        return json.dumps(res)
    
    def _is_finished(self) -> bool:
        '''
        Return True if all materials are submitted.
        '''
        for material, amount in self.quest_meta.materials_requirement.items():
            if material not in self.current_status or self.current_status[material] < amount:
                return False
        return True
    

if __name__ == '__main__':
    quest_meta = QuestMeta(
        name="lumber_hunt",
        description="Get 10 lumber to build your first timber house.",
        hint="Check your inventory to see if you have enough lumber. Felwood is a good place to find lumber.",
        materials_requirement={
            Lumber(): 10,
        },
    )
    quest = Quest(quest_meta)
    
    submission_0 = Msg(
        name="submission_0",
        content={
            Lumber(possesser_id="kerryyu"): 5,
        },
        role="user",
    )
    
    print(quest(submission_0).content)
    
    time.sleep(1)
    
    submission_1 = Msg(
        name="submission_1",
        content={
            Lumber(possesser_id="kerryyu"): 5,
        },
        role="user",
    )
    
    print(quest(submission_0).content)
    
    time.sleep(1)