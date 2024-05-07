# -*- coding: utf-8 -*-
"""Game flow loop control."""

# -*- coding: utf-8 -*-
"""A werewolf game implemented by agentscope."""
from functools import partial
from typing import Literal

from loguru import logger
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.pipelines.functional import sequentialpipeline
import agentscope
import os 

from resources import Quest, QuestMeta, Lumber

FILE_DIR_PATH = r"E:\WorkDir\llm_apps\agentscope\myapps\game_companion"
MAX_GAME_ROUND = 3

# pylint: disable=too-many-statements
def main() -> None:
    """quest game"""
    # default settings
    HostMsg = partial(Msg, name="Moderator", role="assistant", echo=True) # default HostMsg parameters
    # read model and agent configs, and initialize agents automatically
    npcs = agentscope.init(
        model_configs=f"{FILE_DIR_PATH}/configs/model_configs.json",
        agent_configs=f"{FILE_DIR_PATH}/configs/agent_configs.json",
        logger_level="INFO",
    )
    npc = npcs[0]

    # new Quest for npcs
    quest_meta = QuestMeta(
        name="lumber_hunt",
        agent_id=npc.name,
        description="Submit 10 lumber to build your first timber house",
        hint="Submit quest materials. Make sure your response format complies with required format.",
        materials_requirement={
            Lumber(): 10,
        },
    )
    quest: Quest = Quest(quest_meta)
    
    # tell npcs about goals and hints
    # looping until quest is accomplished
    msg = HostMsg(content=("{}, 你现在拥有10根木头。你的目标是完成一个任务。任务描述：{}。使用以下格式回复\n"
                           "{{\n"
                           '    "speak": "你的思考过程",'
                           '    "agent_id": "你的名字",'
                           '   "material_submission": {{'
                           '        "材料名": 材料数目'
                           '    }}"\n'
                           "}}。例如\n"
                           "{{\n"
                           '    "speak": "任务需要10根木头，当前我有1根，提交任务看看会发生什么",'
                           '    "agent_id": "npc1",'
                           '   "material_submission": {{'
                           '        "lumber": 1'
                           '    }}"\n'
                           "}}\n"
                           ).format(npc.name, quest.introduction()))
    while not quest.is_accomplished():
        msg = npc(msg)
        msg = quest(msg)
        
    logger.info('Congrats! The quest has been accomplished!')


if __name__ == "__main__":
    main()