# -*- coding: utf-8 -*-
"""A werewolf game implemented by agentscope."""
from functools import partial

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
        logger_level="DEBUG",
    )
    roles = ["werewolf", "werewolf", "villager", "villager", "seer", "witch"]
    wolves, witch, seer = survivors[:2], survivors[-1], survivors[-2]

    # start the game
    for _ in range(1, MAX_GAME_ROUND + 1):
        # night phase, werewolves discuss
        hint = HostMsg(content=Prompts.to_wolves.format(n2s(wolves)))
        with msghub(wolves, announcement=hint) as hub:
            for _ in range(MAX_WEREWOLF_DISCUSSION_ROUND):
                x = sequentialpipeline(wolves)
                if x.get("agreement", False):
                    break

            # werewolves vote
            hint = HostMsg(content=Prompts.to_wolves_vote)
            votes = [
                extract_name_and_id(wolf(hint).content)[0] for wolf in wolves
            ]
            # broadcast the result to werewolves
            dead_player = [majority_vote(votes)]
            hub.broadcast(
                HostMsg(content=Prompts.to_wolves_res.format(dead_player[0])),
            )

        # witch
        healing_used_tonight = False
        if witch in survivors:
            if healing:
                hint = HostMsg(
                    content=Prompts.to_witch_resurrect.format_map(
                        {
                            "witch_name": witch.name,
                            "dead_name": dead_player[0],
                        },
                    ),
                )
                if witch(hint).get("resurrect", False):
                    healing_used_tonight = True
                    dead_player.pop()
                    healing = False

            if poison and not healing_used_tonight:
                x = witch(HostMsg(content=Prompts.to_witch_poison))
                if x.get("eliminate", False):
                    dead_player.append(extract_name_and_id(x.content)[0])
                    poison = False

        # seer
        if seer in survivors:
            hint = HostMsg(
                content=Prompts.to_seer.format(seer.name, n2s(survivors)),
            )
            x = seer(hint)

            player, idx = extract_name_and_id(x.content)
            role = "werewolf" if roles[idx] == "werewolf" else "villager"
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
            votes = [
                extract_name_and_id(_(hint).content)[0] for _ in survivors
            ]
            vote_res = majority_vote(votes)
            # broadcast the result to all players
            result = HostMsg(content=Prompts.to_all_res.format(vote_res))
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