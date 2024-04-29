# -*- coding: utf-8 -*-
"""A werewolf game implemented by agentscope."""
from functools import partial
from typing import Literal

from prompt import Prompts
from werewolf_utils import (
    check_winning,
    update_alive_players,
    majority_vote,
    extract_name_and_id,
    n2s,
)
from agentscope.message import Msg
from agentscope.msghub import msghub
from agentscope.pipelines.functional import sequentialpipeline
import agentscope
import os 

FILE_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
# playing roles definition
ROLE_WEREWOLF = "狼人"
ROLE_VILLAGER = "村民"
ROLE_SEER = "预言家"
ROLE_WITCH = "女巫"

# pylint: disable=too-many-statements
def main() -> None:
    """werewolf game"""
    # default settings
    HostMsg = partial(Msg, name="Moderator", role="assistant", echo=True)
    healing, poison = True, True
    MAX_WEREWOLF_DISCUSSION_ROUND = 3
    MAX_GAME_ROUND = 6
    # read model and agent configs, and initialize agents automatically
    survivors = agentscope.init(
        model_configs=f"{FILE_DIR_PATH}/configs/model_configs.json",
        agent_configs=f"{FILE_DIR_PATH}/configs/agent_configs.json",
        logger_level="INFO",
    )
    roles = [ROLE_WEREWOLF, ROLE_WEREWOLF, ROLE_VILLAGER, ROLE_VILLAGER, ROLE_SEER, ROLE_WITCH]
    wolves, witch, seer = survivors[:2], survivors[-1], survivors[-2]

    # start the game
    for _ in range(1, MAX_GAME_ROUND + 1):
        # night phase, werewolves discuss
        hint = HostMsg(content=Prompts.to_wolves.format(n2s(wolves)))
        with msghub(wolves, announcement=hint) as hub:
            for _ in range(MAX_WEREWOLF_DISCUSSION_ROUND): # announcement is sent to each wolf
                x = sequentialpipeline(wolves) # waiting for agreement, if discussion round reaches max, the discussion ends
                if x.get("agreement", False):
                    break

            # werewolves vote
            hint = HostMsg(content=Prompts.to_wolves_vote)
            
            votes = []
            for wolf in wolves:
                name, _, valid = extract_name_and_id(wolf(hint).content)  # only valid player name from reply added to the list
                if valid and len(name) != 0:
                    votes.append(name)
            # broadcast the result to werewolves
            dead_player = [majority_vote(votes)]
            if len(dead_player) == 0:
                hub.broadcast(
                    HostMsg(content=Prompts.to_wolves_res_empty),
                )
            else:
                hub.broadcast(
                    HostMsg(content=Prompts.to_wolves_res.format(dead_player[0])),
                )

        # witch
        healing_used_tonight = False
        if witch in survivors:
            if healing:
                if len(dead_player) == 0:
                    result = Prompts.to_witch_no_dead
                else:
                    result = Prompts.to_witch_has_dead.format_map(
                        {
                            "dead_name": dead_player[0],
                        }
                    )
                    
                hint=HostMsg(content=Prompts.to_witch_resurrect.format_map(
                    {
                        "witch_name": witch.name,
                        "result_and_reply": result,
                    },
                ),)
                if witch(hint).get("resurrect", False):
                    healing_used_tonight = True
                    dead_player.pop()
                    healing = False

            if poison and not healing_used_tonight:
                x = witch(HostMsg(content=Prompts.to_witch_poison))
                if x.get("eliminate", False):
                    name, _, valid = extract_name_and_id(x.content)
                    if valid and len(name) != 0:
                        dead_player.append()
                        poison = False

        # seer
        if seer in survivors:
            hint = HostMsg(
                content=Prompts.to_seer.format(seer.name, n2s(survivors)),
            )
            x = seer(hint)

            player, idx, _ = extract_name_and_id(x.content)
            role = ROLE_WEREWOLF if role[idx] == ROLE_WEREWOLF else ROLE_VILLAGER
            hint = HostMsg(content=Prompts.to_seer_result.format(player, role))
            seer.observe(hint)

        survivors, wolves = update_alive_players(
            survivors,
            wolves,
            dead_player,
        )
        if check_winning(survivors, wolves, "Moderator"):
            break

        # daytime discussion
        content = (
            Prompts.to_all_danger.format(n2s(dead_player))
            if dead_player
            else Prompts.to_all_peace
        )
        hints = [
            HostMsg(content=content),
            HostMsg(content=Prompts.to_all_discuss.format(n2s(survivors))),
        ]
        with msghub(survivors, announcement=hints) as hub:
            # discuss
            x = sequentialpipeline(survivors)

            # vote
            hint = HostMsg(content=Prompts.to_all_vote.format(n2s(survivors)))
            
            votes = []
            for survivor in survivors:
                name, _, valid = extract_name_and_id(survivor(hint).content) 
                if valid and len(name) != 0:
                    votes.append(name)
            
            vote_res = majority_vote(votes)
        
            # broadcast the result to all players
            if len(vote_res) == 0:
                result = HostMsg(content=Prompts.to_all_res_no_voteout)
            else:
                result = HostMsg(content=Prompts.to_all_res_has_voteout.format(vote_res))
            hub.broadcast(result)

            survivors, wolves = update_alive_players(
                survivors,
                wolves,
                vote_res,
            )

            if check_winning(survivors, wolves, "Moderator"):
                break

            hub.broadcast(HostMsg(content=Prompts.to_all_continue))


if __name__ == "__main__":
    # content = ('{'
    # '"thought": "基于当前的局势和玩家们的互动，我倾向于选择[Player3]作为今晚的目标。他似乎在尝试构建某种联盟，而且在讨论中也表现得较为积极。",'
    # '"speak": "我建议我们今晚杀掉Player3。"'
    # '}')
    # print(extract_name_and_id(content)[0])
    main()