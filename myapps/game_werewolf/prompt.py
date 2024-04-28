"""用于记录提示，将由配置替换"""

class Prompts:
    """狼人游戏的提示"""

    to_wolves = (
        "{}, 你正在参与狼人杀游戏。你的身份是狼人，今晚必须杀死一位玩家。如果你是唯一的狼人，则直接选择杀死一个玩家。否则，"
        "与你的队友讨论并达成一致。请使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "想法总结为发言",\n'
        '    "agreement": "讨论是否达成了一致'
        '(true/false)"\n'
        "}}"
    )

    to_wolves_vote = (
        "你选择杀死哪个玩家？选择一个玩家并使用以下格式回复\n"
        "{\n"
        '   "thought": "想法",\n'
        '   "speak": "玩家名。例如 Player1"\n'
        "}"
    )

    to_wolves_res = "得票最多的玩家是{}。"

    to_witch_resurrect = (
        "{witch_name}，你正在参与狼人杀游戏。你的身份是女巫。今晚{dead_name}被杀死了。"
        "你想要复活{dead_name}吗？请使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "想法总结为发言",\n'
        '    "resurrect": true/false\n'
        "}}"
    )

    to_witch_poison = (
        "你想投毒杀死一个玩家吗？请使用以下json格式回复\n"
        "{\n"
        '    "thought": "想法", \n'
        '    "speak": "想法总结为发言",\n'
        '    "eliminate": true/false\n'
        "}"
    )

    to_seer = (
        "{}, 你正在参与狼人杀游戏。你的身份是预言家。今晚你想查看哪个玩家的身份？选择一个玩家并使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法" ,\n'
        '    "speak": "玩家名。例如 Player1"\n'
        "}}"
    )

    to_seer_result = "好的，{}的角色是{}。"

    to_all_danger = (
        "白天即将来临，所有玩家睁开你们的眼睛。昨晚，"
        "以下玩家死亡：{}。"
    )

    to_all_peace = (
        "白天即将来临，所有玩家睁开你们的眼睛。昨晚是"
        "平安夜，没有玩家死亡。"
    )

    to_all_discuss = (
        "现在活着的玩家是{}。根据游戏规则和你的角色，"
        "基于情况和你获得的信息，为了赢得游戏而投票淘汰一个玩家，你想要对其他人说什么"
        "？你可以决定是否透露你的角色。请使用以下格式回复\n"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "想法总结"\n'
        "}}"
    )

    to_all_vote = (
        "现在活着的玩家是{}。根据游戏规则和你的角色，"
        "基于情况和你获得的信息，为了赢得游戏，必须投票淘汰一个玩家，"
        "请在活着的玩家中选择一个你认为是狼人的玩家并投票。选择一个玩家并使用以下格式回复"
        "{{\n"
        '    "thought": "想法",\n'
        '    "speak": "玩家名。例如 Player1"\n'
        "}}"
    )

    to_all_res = "{} 被淘汰了。"

    to_all_wolf_win = (
        "狼人获胜并接管了村庄。下次好运！"
    )

    to_all_village_win = (
        "游戏结束。狼人被击败，村庄再次安全了！"
    )

    to_all_continue = "游戏继续。"