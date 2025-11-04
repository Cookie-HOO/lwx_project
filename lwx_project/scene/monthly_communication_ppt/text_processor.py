def find_max_and_up_or_down(bank2amount, bank2tongbi):
    """
    bank2amount: {"工银安盛": 1, "农银人寿": 2, "中银三星": 3, "建信人寿": 4}
    bank2tongbi: {"工银安盛": 0.1, "农银人寿": 0.2, "中银三星": 0.3, "建信人寿": 0.4}
    """
    max_amount = -1
    max_bank = ""
    for bank, amount in bank2amount.items():
        amount = float(amount)
        if amount > max_amount:
            max_amount = amount
            max_bank = bank

    tongbi_up = [b for b, v in bank2tongbi.items() if float(v) > 0]
    tongbi_down = [b for b, v in bank2tongbi.items() if float(v) < 0]
    return max_bank, round(max_amount, 3), float(bank2tongbi.get(max_bank)), tongbi_up, tongbi_down

def make_tongbi_text(tongbi_up, tongbi_down, topic):
    # 都下降
    if len(tongbi_up) == 0:
        return f"四家银行系子公司{topic}同比均下降。"
    # 都上升
    elif len(tongbi_down) == 0:
        return f"四家银行系子公司{topic}同比均下降。"
    # 有升有降
    return "、".join(tongbi_up) + topic + "同比上升；" + "、".join(tongbi_down) + "同比下降。"

def page4_amount(bank2amount, bank2tongbi):
    pass

def page4_tongbi(bank2amount, bank2tongbi):
    pass

def page5_amount(bank2amount, bank2tongbi):
    pass

def page5_tongbi(bank2amount, bank2tongbi):
    pass