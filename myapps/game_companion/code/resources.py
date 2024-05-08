# -*- coding: utf-8 -*-
"""Resources definition and implementation, including quests & materials / areas and background knowledge."""

from functools import partial
import json
import math
import time
from typing import Any, Dict, Sequence
import uuid
from loguru import logger

from agentscope.agents import AgentBase
from agentscope.message import Msg


class Error(str):
    def __init__(self, msg="") -> None:
        self.msg = msg
        
    def __str__(self) -> str:
        return self.msg


class MaterialItem(dict):
    '''
    An material item can be obtained by agents via a variety of approaches.
    '''
    def __init__(self, 
                 name="",
                 description="",
                 possesser_id="",
                 type_id="",
                 **kwargs) -> None:
        self.name = name
        self.item_id = f"{self.name}_{uuid.uuid4().hex}"
        self.type_id = type_id
        self.description = description
        self.possesser_id = possesser_id
        
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
        return f"{self.type_id}"


class Lumber(MaterialItem):
    name = "lumber"
    description="A piece of wood."
    type_id = "lumber"
    
    def __init__(self, 
                 possesser_id="",) -> None:
        super().__init__(name=self.name,
                         description=self.description,
                         type_id=self.type_id,
                         possesser_id=possesser_id)
        
        
def material_item_factory(item_type_id: str, 
                          possesser_id: str,
                          number: int = 0) -> Sequence[MaterialItem]:
    '''
    Generate material item(s)
    '''
    material_dict = {
        Lumber.type_id: Lumber,
    }
    
    return [material_dict[item_type_id](possesser_id=possesser_id) for _ in range(math.floor(number))]
    

class QuestMeta(dict):
    def __init__(self, 
                 name="basic_quest",
                 agent_id="",
                 description="It's a quest base",
                 hint="You need to do something.",
                 unfinished_msg="The quest is not finished yet. Current status: {current_status}",
                 finished_msg="You have finished the quest!",
                 materials_requirement: Dict[MaterialItem, int] = {},
                 **kwargs) -> None:
        self.name = name
        self.agent_id = agent_id
        self.description = description
        self.hint = hint
        self.unfinished_msg = unfinished_msg
        self.finished_msg = finished_msg
        self.materials_requirement = materials_requirement
        
        self._quest_id = self.__class__.generate_id()
        
        self.update(kwargs)
        
    @classmethod
    def generate_id(cls) -> str:
        return f"{cls.__name__}_{uuid.uuid4().hex}"
    
    @property
    def quest_id(self) -> str:
        return self._quest_id
    
    def prompt(self) -> str:
        requirement_msgs = []
        for k, v in self.materials_requirement.items():
            requirement_msgs.append(f"{str(k)}: {v}")
            
        return f"{self.name}: {self.description}. requirement: {{{",".join(requirement_msgs)}}}"

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
    name_prefix = "Quest-"
    '''
    A Quest is a specific goal or objective, assigned by player to an agent, that requires submitting certain number and type of materials.
    '''
    def __init__(self, 
                 quest_meta: QuestMeta=QuestMeta()) -> None:
        self.quest_meta = quest_meta
        self.current_status: Dict = {} # {material: amount}
        
        super().__init__(name=self.name_prefix+quest_meta.name, use_memory=False)
    
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
        return_content = {
            "valid": False,
            "finished": False,
        }
        ReturnMsg = partial(Msg, name=self.name, role="assistant")
        Echo = partial(Msg, name=self.name, role="assistant", echo=True)
        err = self._validate(x)
        if err != None:
            logger.error(f"Invalid submission: {err}")
            return_content["message"] = f"Invalid submission: {err}"
            Echo(content=return_content["message"]) # echo
            return ReturnMsg(content=return_content)
            
        return_content["valid"] = True
        
        submission_agent_id = x['agent_id']
        material_submission: Dict = x['material_submission']
        
        # create material items as described in submission msg
        for material_type_id, amount in material_submission.items(): 
            if amount <= 0:
                continue
            materials = material_item_factory(material_type_id, submission_agent_id, amount)
            if materials[0] in self.quest_meta.materials_requirement:
                self.current_status[materials[0]] = self.current_status.get(materials[0], 0) + amount
        
        # check if task is accomplished
        if self.is_accomplished():
            return_content["message"] = self.quest_meta.finished_msg
            return_content["finished"] = True
        else:
            return_content["message"] = self.quest_meta.unfinished_msg.format_map({
                "current_status": self._current_status_str(),
            })
            return_content["hint"] = self.quest_meta.hint
        
        Echo(content=return_content["message"]) # echo
        return ReturnMsg(content=return_content)
      
    def is_accomplished(self) -> bool:
        '''
        Return True if all materials are submitted.
        '''
        for material, amount in self.quest_meta.materials_requirement.items():
            if material not in self.current_status or self.current_status[material] < amount:
                return False
        return True
    
    def introduction(self) -> str:
        '''
        Return the introduction of the quest.
        '''
        return self.quest_meta.prompt()
        
    def _validate(self, x: dict) -> Error:
        # TODO: validate if x is compatible
        if not isinstance(x, dict):
            return Error("x must be a dict")
        
        if "agent_id" not in x or x["agent_id"] != self.quest_meta.agent_id:
            return Error("agent_id not existed or invalid")
        if "material_submission" not in x or not isinstance(x["material_submission"], dict):
            return Error("material_submission not existed")
            
        return None
    
    def _current_status_str(self) -> str:
        '''
        Return material and amount in string format
        '''
        res = {}
        for material, amount in self.current_status.items():
            res[str(material)] = amount
        return json.dumps(res)   

    
def submit(quest: Quest, submission_msg: Msg):
    print(quest(submission_msg).content)
    time.sleep(1)
    

if __name__ == '__main__':
    quest_meta = QuestMeta(
        name="lumber_hunt",
        agent_id="kerryyu",
        description="Get 10 lumber to build your first timber house.",
        hint="Check your inventory to see if you have enough lumber. Felwood is a good place to find lumber.",
        materials_requirement={
            Lumber(): 10,
        },
    )
    quest = Quest(quest_meta)
    
    print(quest.introduction())
    
    submit(quest=quest, 
           submission_msg=Msg(
                name="submission_0",
                content={
                    "agent_id": "kerryyu",
                    "material_submission": {
                        "lumber": 5,
                    }
                },
                role="user",
           ),
    )
    
    submit(quest=quest, 
           submission_msg=Msg(
                name="submission_1",
                content={
                    "agent_id": "kerryyu",
                    "material_submission": {
                        "lumber": 5,
                    }
                },
                role="user",
           ),
    )