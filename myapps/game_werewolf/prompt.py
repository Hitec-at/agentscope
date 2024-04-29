"""用于记录提示，将由配置替换"""

class Prompts:
    """狼人游戏的提示"""

    to_wolves = (
        "{}，你们是狼人玩家，轮到你们行动。请狼人确认同伴身份和己方剩余人数。如果你是唯一的狼人，则直接选择淘汰一个玩家。否则，"
        "与你的队友讨论并达成一致。请使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "发言内容",\n'
        '    "agreement": "讨论是否达成了一致'
        '(true/false)"\n'
        "}}"
    )

    to_wolves_vote = (
        "你们选择淘汰哪个玩家？选择一个玩家并使用以下格式回复\n"
        "{\n"
        '   "thought": "想法",\n'
        '   "speak": "只能是玩家名"\n'
        "}"
    )

    to_wolves_res = "得票最多的玩家是{}。"
    to_wolves_res_empty = "没有玩家被淘汰。"

    to_witch_resurrect = (
        "{witch_name}，你的身份是女巫，轮到你的行动。今晚{result_and_reply}"
    )
    to_witch_has_dead = (
        "{dead_name}被淘汰了。你有一瓶解药，"
        "你想要复活{dead_name}吗？请使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "发言内容",\n'
        '    "resurrect": true/false\n'
        "}}"
    )
    to_witch_no_dead = (
        "没有人死亡"
    )

    to_witch_poison = (
        "你想投毒淘汰一个玩家吗？请使用以下json格式回复\n"
        "{\n"
        '    "thought": "想法", \n'
        '    "speak": "发言内容",\n'
        '    "eliminate": true/false\n'
        "}"
    )

    to_seer = (
        "{}, 你的身份是预言家。今晚你想查看哪个玩家的身份？选择一个玩家并使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法" ,\n'
        '    "speak": "只能是玩家名"\n'
        "}}"
    )

    to_seer_result = "好的，{}的角色是{}。"

    to_all_danger = (
        "白天即将来临，所有玩家睁开你们的眼睛。昨晚，"
        "以下玩家被淘汰：{}。"
    )

    to_all_peace = (
        "白天即将来临，所有玩家睁开你们的眼睛。昨晚是"
        "平安夜，没有玩家被淘汰。"
    )

    to_all_discuss = (
        "现在仍在游戏中的玩家是{}。根据游戏规则和你的角色，"
        "基于情况和你获得的信息，为了赢得游戏而投票淘汰一个玩家，你想要对其他人说什么"
        "？你可以决定是否透露你的角色。请使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "发言内容"\n'
        "}}"
    )

    to_all_vote = (
        "现在仍在游戏中的玩家是{}。根据游戏规则和你的角色，"
        "基于情况和你获得的信息，为了赢得游戏，必须投票淘汰一个玩家，"
        "请在仍在游戏中的玩家中，选择一个玩家并投票。使用以下格式回复"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "只能是玩家名"\n'
        "}}"
    )

    to_all_res_has_voteout = "{} 被淘汰了。"
    to_all_res_no_voteout = "没有玩家被淘汰。"

    to_all_wolf_win = (
        "狼人获胜并接管了村庄。下次好运！"
    )

    to_all_village_win = (
        "游戏结束。狼人被击败，村庄再次安全了！"
    )

    to_all_continue = "游戏继续。"