hoa_input = """
State: 0
[t] 0
State: 1
[!0] 0
[0&1] 2
State: 2
[1] 2
"""

hoa_input = """
State: 0 {0}
[t] 0
State: 1
[1] 0
[!1] 1
State: 2
[0&1] 0
[0&!1] 1
[!0&!1] 2
[!0&1] 3
State: 3
[0] 0
[!0] 3
"""
hoa_input = """
HOA: v1
name: "FGa1"
States: 2
Start: 0
AP: 1 "a1"
acc-name: Buchi
Acceptance: 1 Inf(0)
properties: trans-labels explicit-labels state-acc stutter-invariant
properties: very-weak
--BODY--
State: 0
[t] 0
[0] 1
State: 1 {0}
[0] 1
--END--
    """

def parse_condition(condition_str):
    """
    解析条件字符串，将其标准化以便比较和映射。
    支持以下形式的条件：
    - 单一命题：'0', '1', '!0'
    - 复合命题：'0&1', '!0&1', '0&!1', '!0&!1'
    - 特殊命题：'t'（恒为真）
    """
    condition_str = condition_str.strip()
    if condition_str == 't':
        return 'True'  # 用字符串'True'表示恒为真
    literals = condition_str.split('&')
    literals = sorted(literal.strip() for literal in literals)
    return '&'.join(literals)


def convert_hoa_to_ba_format(hoa_input):
    """
    将HOA格式转换为BA格式。
    """
    lines = hoa_input.strip().split('\n')
    print(f"hoa_input={hoa_input}")
    print(f"lines = {lines}")
    current_state = None
    accepting_states = set()
    transitions = []
    initial_state = None
    condition_to_input = {}
    input_index = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue  # 跳过空行
        if line.startswith("State:"):
            parts = line.split()
            current_state = int(parts[1])
            if len(parts) > 2 and '{' in parts[2]:
                accepting_states.add(current_state)
            if initial_state is None:
                initial_state = current_state
        elif '[' in line and ']' in line:
            condition_part, target_state_part = line.split(']')
            condition_raw = condition_part[1:]  # 去除开头的 '['
            target_state = int(target_state_part.strip())
            condition = parse_condition(condition_raw)
            if condition not in condition_to_input:
                condition_to_input[condition] = f"a{input_index}"
                input_index += 1
            input_symbol = condition_to_input[condition]
            transitions.append(f"{input_symbol},[{current_state}]->[{target_state}]")

    # 生成BA格式的输出
    output_lines = []
    output_lines.append(f"[{initial_state}]")
    output_lines.extend(transitions)
    for state in accepting_states:
        output_lines.append(f"[{state}]")

    return '\n'.join(output_lines)


def save_to_ba_file(content, filename="output.ba"):
    """
    将内容保存为BA文件。
    """
    with open(filename, 'w') as file:
        file.write(content)


def main():
    """
    主函数，执行转换和保存操作。
    """
    result = convert_hoa_to_ba_format(hoa_input)
    save_to_ba_file(result)
    print("转换完成，结果已保存为 output.ba")
    print("转换结果：")
    print(result)


if __name__ == "__main__":
    main()
