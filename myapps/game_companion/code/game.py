# -*- coding: utf-8 -*-
"""Game flow loop control."""

# -*- coding: utf-8 -*-
"""A werewolf game implemented by agentscope."""
from functools import partial
import time
from typing import Literal

from loguru import logger
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.pipelines.functional import sequentialpipeline
import agentscope
import os 

from resources import Quest, QuestMeta, Lumber

FILE_DIR_PATH = r"E:\WorkDir\llm_apps\agentscope\myapps\game_companion"
MAX_GAME_ROUND = 5

# pylint: disable=too-many-statements
def main() -> None:
    """quest game"""
    # default settings
    HostMsg = partial(Msg, name="GameManager", role="assistant", echo=True) # default HostMsg parameters
    # read model and agent configs, and initialize agents automatically
    npcs = agentscope.init(
        model_configs=f"{FILE_DIR_PATH}/configs/model_configs.json",
        agent_configs=f"{FILE_DIR_PATH}/configs/agent_configs.json",
        logger_level="INFO",
    )

    # new Quest for npcs
    quests = [Quest(QuestMeta(
        name="寻找木材",
        agent_id=npc.name,
        description="提交10个木材，建造你的小木屋",
        hint="请提交任务材料。确保回复格式符合要求。",
        unfinished_msg="你已成功提交任务材料，但任务还未完成。已提交：{current_status}",
        finished_msg="恭喜，你的任务已经完成！",
        materials_requirement={
            Lumber(): 10,
        },
    )) for npc in npcs]
    
    # tell npcs about goals and hints
    # looping until quest is accomplished
    guide_msgs = [HostMsg(content=("{}, 你现在拥有10根木头。你的目标是分为1~5次行动完成任务。任务描述：{}。使用以下格式回复\n"
                           "{{\n"
                           '    "speak": "你的思考过程，对其它玩家游戏进程的看法",'
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
                           ).format(npc.name, quest.introduction())) for npc, quest in zip(npcs, quests)]
    
    
    with msghub(npcs) as hub:
        accomplished_quest = set()
        cur_round = 0
        while len(accomplished_quest) < len(quests) and cur_round < MAX_GAME_ROUND:            
            cur_round += 1
            hub.broadcast(HostMsg(content=f"第{cur_round}轮游戏开始。{game_status(cur_round, len(accomplished_quest), len(quests))}"))
            for i in range(len(npcs)):
                npc = npcs[i]
                quest: Quest = quests[i]
                # pre-inspeect quest status, skip to avoid oversubmission
                if quest.is_accomplished():
                    accomplished_quest.add(quest)
                    continue
                
                msg = npc(guide_msgs[i])
                guide_msgs[i] = quest(msg)
                
                if quest.is_accomplished():
                    accomplished_quest.add(quest)
                
            time.sleep(3)
                
        logger.info(f"游戏结束。{game_status(cur_round, len(accomplished_quest), len(quests))}")    
        
        
def game_status(cur_round, accomplished_quest_num, quests_num) -> str:
    return f'\n\n游戏轮次：{cur_round}/{MAX_GAME_ROUND}，任务完成情况：{accomplished_quest_num}/{quests_num}\n\n'            
        


if __name__ == "__main__":
    main()