"""
改进版 HOA -> BA 转换器：支持标准 HOA 头部（HOA:、States:、Start:、AP:、Acceptance: 等），
并正确解析状态、命题变量、接受状态等信息。
相对于v1 增加多个accepting state的处理
"""

import re
from os.path import dirname, abspath, join
from subprocess import check_output


def parse_condition(condition_str, ap_list):
    cond = condition_str.strip()
    if cond == 't':
        return 'True'

    # 匹配数字或者!数字
    pattern = re.compile(r'!?\d+')

    def repl(m):
        token = m.group(0)
        if token.startswith('!'):
            idx = int(token[1:])
            return f"!{ap_list[idx]}"
        else:
            idx = int(token)
            return ap_list[idx]

    # 只替换数字和!数字，不改变其他字符
    parsed = pattern.sub(repl, cond)
    return parsed


def convert_hoa_to_ba_format(hoa_input):
    lines = hoa_input.strip().split('\n')

    ap_list = []
    initial_states = []
    accepting_sets = set()
    acceptance_set_ids = set()
    transitions = []
    condition_to_input = {}
    input_index = 0
    current_state = None
    reading_body = False
    print(f"hoa_input={hoa_input}")
    print(f"lines = {lines}")

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line == '--BODY--':
            reading_body = True
            continue

        if not reading_body:
            if line.startswith('AP:'):
                # Extract everything within the "" into a list, strictly following the order of appearance in the string.
                ap_list = re.findall(r'"(.*?)"', line)
            elif line.startswith('Start:'):
                initial_states = list(map(int, line[len('Start:'):].strip().split()))
            elif line.startswith('Acceptance:'):
                # `re.findall(r'Inf\((\d+)\)', line)` will return a list containing all the matched numeric string; `map(int, matches)` converts the strings to integers.
                acceptance_set_ids = set(map(int, re.findall(r'Inf\((\d+)\)', line)))

        else:
            if line.startswith('State:'):
                parts = line.split()
                current_state = int(parts[1])
                if len(parts) > 2 and '{' in parts[2]:
                    # accepting_sets.add(current_state)
                    acc_indices = set(map(int, re.findall(r'\d+', parts[2]))) #查看 state: "{}" 里面的数字
                    if acc_indices & acceptance_set_ids: # "{}" 里面的数字 和 acceptance_set_ids集合是否有交集
                        accepting_sets.add(current_state)
            elif '[' in line and ']' in line:
                condition_part, target_state_part = line.split(']')
                condition_raw = condition_part[1:]
                target_state = int(target_state_part.strip())
                condition = parse_condition(condition_raw, ap_list)
                if condition not in condition_to_input:
                    # condition_to_input[condition] = f"a{input_index}"
                    condition_to_input[condition] = f"{condition}"
                    input_index += 1
                input_symbol = condition_to_input[condition]
                transitions.append(f"{input_symbol},[{current_state}]->[{target_state}]")

    # 构造输出
    output_lines = []
    for init in initial_states:
        output_lines.append(f"[{init}]")
    output_lines.extend(transitions)
    for acc in accepting_sets:
        output_lines.append(f"[{acc}]")
    return '\n'.join(output_lines)


# def save_to_ba_file(content, filename="output_complex.ba"):
#     with open(filename, 'w') as file:
#         file.write(content)
def save_to_ba_file(content: str, filename: str):
    """
    将 BA 内容保存为 .ba 文件
    :param content: 要写入文件的内容（字符串）
    :param filename: 保存的文件名，例如 'my_output.ba'
    """
    with open(filename, 'w') as file:
        file.write(content)


def main():
    hoa_input = """
HOA: v1
States: 4
Start: 0
AP: 2 "p" "q"
Acceptance: 1 Inf(0)
--BODY--
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
Output: HOA: v1
name: "FGa1"
States: 3
Start: 0
AP: 1 "a1"
acc-name: Buchi
Acceptance: 1 Inf(0)
properties: trans-labels explicit-labels state-acc complete
properties: stutter-invariant very-weak
--BODY--
State: 0
[t] 0
[0] 1
State: 1 {0}
[0] 1
[!0] 2
State: 2 
[t] 2
--END--
    """
    hoa_input_complex = """
HOA: v1
name: "(F((p1 & Fp2) | (!p1 & G!p2)) & XXFp2) | (G((p1 & G!p2) | (!p1 & Fp2)) & XXG!p2)"
States: 12
Start: 0
AP: 2 "p1" "p2"
acc-name: Buchi
Acceptance: 1 Inf(0)
properties: trans-labels explicit-labels state-acc complete very-weak
--BODY--
State: 0
[0] 1
[!0&!1] 2
[!0] 3
[!0&1] 4
[0&!1] 5
State: 1
[t] 6
State: 2
[!0&1] 5
[0 | !1] 11
State: 3
[0] 6
[!0] 8
State: 4
[!0&1 | 0&!1] 5
[!0&!1 | 0&1] 11
State: 5 {0}
[0&!1] 5
[!0 | 1] 11
State: 6
[!1] 6
[1] 7
State: 7 {0}
[t] 7
State: 8
[0&!1] 6
[0&1] 7
[!0&!1] 8
[!0&1] 9
State: 9
[0&!1] 6
[0&1] 7
[!0 | !1] 9
[!0&!1] 10
State: 10 {0}
[!1] 10
[1] 11
State: 11
[t] 11
--END--
        """
    hoa_dong = """
HOA: v1
name: "G(Fupload & Fgather & Frecharge)"
States: 4
Start: 0
AP: 3 "upload" "gather" "recharge"
acc-name: Buchi
Acceptance: 1 Inf(0)
properties: trans-labels explicit-labels state-acc complete
properties: deterministic stutter-invariant
--BODY--
State: 0 {0}
[0&1&2] 0
[!2] 1
[!1&2] 2
[!0&1&2] 3
State: 1
[0&1&2] 0
[!2] 1
[!1&2] 2
[!0&1&2] 3
State: 2
[0&1] 0
[!1] 2
[!0&1] 3
State: 3
[0] 0
[!0] 3
--END--
            """
    result = convert_hoa_to_ba_format(hoa_dong)
    filename = "yiwei_CDC.ba"  # 文件名可按需要更改
    save_to_ba_file(result, filename)
    print(f'转换完成，结果已保存为{filename}')
    print("转换结果：")
    print(result)


if __name__ == "__main__":
    main()
