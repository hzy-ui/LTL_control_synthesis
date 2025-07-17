"""
改进版 HOA -> BA 转换器：支持标准 HOA 头部（HOA:、States:、Start:、AP:、Acceptance: 等），
并正确解析状态、命题变量、接受状态等信息。
"""

import re
from os.path import dirname, abspath, join
from subprocess import check_output


def parse_condition(condition_str, ap_list):
    condition_str = condition_str.strip()
    if condition_str == 't':
        return 'True'
    literals = condition_str.split('&')
    parsed = []
    for lit in literals:
        lit = lit.strip()
        if lit.startswith('!'):
            index = int(lit[1:])
            parsed.append(f"!{ap_list[index]}")
        else:
            index = int(lit)
            parsed.append(ap_list[index])
    return '&'.join(sorted(parsed))


def convert_hoa_to_ba_format(hoa_input):
    lines = hoa_input.strip().split('\n')

    ap_list = []
    initial_states = []
    accepting_sets = set()
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
                ap_list = re.findall(r'"(.*?)"', line)
            elif line.startswith('Start:'):
                initial_states = list(map(int, line[len('Start:'):].strip().split()))
            elif line.startswith('Acceptance:'):
                acc_nums = re.findall(r'Inf\((\d+)\)', line)
                print(f"acc_nums ={acc_nums}")
                accepting_sets.update(map(int, acc_nums))
        else:
            if line.startswith('State:'):
                parts = line.split()
                current_state = int(parts[1])
                if len(parts) > 2 and '{' in parts[2]:
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


def save_to_ba_file(content, filename="output.ba"):
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
HOA: v1
name: "Fblue_room & Fyellow_room"
States: 4
Start: 2
AP: 2 "blue_room" "yellow_room"
acc-name: Buchi
Acceptance: 1 Inf(0)
properties: trans-labels explicit-labels state-acc complete
properties: deterministic stutter-invariant terminal very-weak
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
--END--
    """
    result = convert_hoa_to_ba_format(hoa_input)
    save_to_ba_file(result)
    print("转换完成，结果已保存为 output.ba")
    print("转换结果：")
    print(result)


if __name__ == "__main__":
    main()
