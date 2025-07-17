import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import re

def parse_custom_ba_with_multiple_states(filename):
    G = nx.MultiDiGraph()
    G = nx.DiGraph()
    initial_states = set()
    accepting_states = set()
    transitions = []

    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip() != '']

    # 将所有转移和状态行分开
    transition_lines = []
    state_lines = []

    for line in lines:
        if "," in line and "->" in line:
            transition_lines.append(line)
        elif re.fullmatch(r"\[\d+\]", line):
            state_lines.append(line)
        else:
            print(f"Skipping unknown line: {line}")

    # 判断初始状态和接受状态
    # 规则：所有 state_lines 出现在 transition_lines 前的为初始状态；之后的为接受状态
    # 考虑没有任何转移语句， transition_lines = []， 不能去访问 transition_lines[0]，否则会 报错 IndexError， 所以所有 []都在前面，都被判为初始状态
    first_transition_index = lines.index(transition_lines[0]) if transition_lines else len(lines)
    for i, line in enumerate(lines):
        if re.fullmatch(r"\[\d+\]", line):
            state = re.findall(r"\d+", line)[0]
            if i < first_transition_index:
                initial_states.add(state)
            else:
                accepting_states.add(state)

    # 添加边
    for line in transition_lines:
        try:
            label, trans = line.split(",")
            src, dst = re.findall(r"\[(\d+)\]", trans)
            G.add_edge(src, dst, label=label.strip())
        except Exception as e:
            print(f"Skipping invalid line: {line}, Error: {e}")

    return G, initial_states, accepting_states

def draw_ba_graph(G, initial_states=None, accepting_states=None):
    pos = nx.spring_layout(G, seed=42)
    pos = nx.kamada_kawai_layout(G)
    node_colors = []

    for node in G.nodes():
        if node in initial_states and node in accepting_states:
            node_colors.append("yellow")  # 初始+接受
        elif node in initial_states:
            node_colors.append("lightgreen")  # 初始状态
        elif node in accepting_states:
            node_colors.append("lightcoral")  # 接受状态
        else:
            node_colors.append("lightblue")  # 普通状态

    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1500, font_size=10)

    edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)} # 构造字典
    print(edge_labels)
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=10) # 看不到loop里的标签
    # 先绘制普通边的标签
    normal_edge_labels = {k: v for k, v in edge_labels.items() if k[0] != k[1]} # 键: 值 for 原始字典中的每个 (键, 值) 如果 键[0] ≠ 键[1]
    nx.draw_networkx_edge_labels(G, pos, edge_labels=normal_edge_labels, font_color='red', font_size=10)

    # 再手动绘制自环的标签
    loop_edges = {k: v for k, v in edge_labels.items() if k[0] == k[1]}

    for (u, v), label in loop_edges.items():
        x, y = pos[u]
        # 偏移一点防止被遮挡
        plt.text(x + 0, y + 0.09, label, fontsize=10, color='red')

    plt.title("Büchi Automaton (Multiple Initial & Accepting States)")
    plt.axis('off')
    # plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # 示例用法 测试用代码只在直接运行此文件时运行
    filename = "output.ba"
    G, init_states, acc_states = parse_custom_ba_with_multiple_states(filename)
    print(G)
    draw_ba_graph(G, init_states, acc_states)