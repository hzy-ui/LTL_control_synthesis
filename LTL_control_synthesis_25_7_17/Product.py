from Buchi_graph import *
from ts import *
import re
import networkx as nx
from collections import deque

def TS_labeling_func(TS, state):
    return TS.nodes[state]['ap']

def match_buchi_label(buchi_label_str: str, ts_label_set: set[str]) -> bool:
    """
    判断 TS 当前 AP 集合是否满足 Buchi 自动机的布尔标签表达式。
    支持 !（非）、&（与）、|（或）、括号 ()。
    note: ap 必须满足 ([a-zA-Z0-9_]+ : 后面跟着一个或多个字母、数字或下划线，也就是 AP 名字（比如 r1, r2, room_3）

    """
    # 如果是 '1'，表示恒真，直接返回 True
    if buchi_label_str.strip() == 'True':
        return True

    # 移除空格
    expr = buchi_label_str.replace(" ", "")

    # 提取 AP 集合
    ap_set = set(re.findall(r'[a-zA-Z0-9_]+', buchi_label_str))

    # ✅ 先处理正的 AP：ap -> 'ap' in ts_label_set  e.g. "!r1 & r2" --> "!'r1' in ts_label_set & 'r2' in ts_label_set"
    for ap in ap_set:
        expr = re.sub(rf'\b{re.escape(ap)}\b', f"'{ap}' in ts_label_set", expr) # re.escape('r*1')  → 'r\*1'

    # ✅ 再处理否定：not 'ap' in ts_label_set（此时 !ap 会变成 not 'ap' in ts_label_set）
    # E.g. "!r1 & r2" --> "!'r1' in ts_label_set & 'r2' in ts_label_set" -->  "not 'r1' in ts_label_set & 'r2' in ts_label_set"
    expr = re.sub(r"!'([^']+)' in ts_label_set", r"not '\1' in ts_label_set", expr)

    # 替换逻辑运算符
    expr = expr.replace("&", " and ").replace("|", " or ")

    # 安全评估表达式
    try:
        result = eval(expr)
    except Exception as e:
        print(f"Error evaluating expression: {expr}")
        raise e

    return result




def build_product_automaton(TS, Buchi, Buchi_init_states, Buchi_acc_states, labeling_func):
    product = nx.DiGraph()

    Q_TS = set(TS.nodes)
    Q_Buchi = set(Buchi.nodes)
    Q_product = set((x, q) for x in Q_TS for q in Q_Buchi)

    # 初始状态
    TS.nodes[(0, 0, 1)]['init'] = True
    Q0_TS = [n for n in TS.nodes if TS.nodes[n].get('init', False)]  # 你可以手动指定 init 状态
    Q0_product = set()

    for x0 in Q0_TS:
        label = TS_labeling_func(TS,  x0)
        for q0 in Buchi_init_states:
            for q in Buchi.successors(q0):
                if match_buchi_label(Buchi[q0][q]['label'], label):  # 注意你这里得匹配 L(x0) G[u][v] 表示 从节点 u 指向 v 的边的属性字典。
                    Q0_product.add((x0, q))

    # 接受状态 F⊗ = X × F
    F_product = set((x, f) for x in Q_TS for f in Buchi_acc_states)

    # 构建 δ⊗
    for (x, q) in Q_product:
        for succ in TS.successors(x):
            u = TS[x][succ]['label'] # 边的label
            label_prime = TS_labeling_func(TS,  succ) #节点的ap
            for q_prime in Buchi.successors(q):
                if Buchi[q][q_prime]['label'] == label_prime:
                    product.add_edge((x, q), (succ, q_prime), label=u)

    return product, Q0_product, F_product

def build_product_automaton_advance(TS, Buchi, Buchi_init_states, Buchi_acc_states):


    product = nx.DiGraph()
    visited = set()
    queue = deque()


    Q0_TS = [n for n in TS.nodes if TS.nodes[n].get('init', False)]
    Q0_product = set()

    # 初始化 product 初始状态（使用 match_buchi_label 判断合法初始对）
    for x0 in Q0_TS:
        label = TS_labeling_func(TS, x0)
        # print(label)
        for q0 in Buchi_init_states:
            for q in Buchi.successors(q0):
                buchi_label = Buchi[q0][q].get('label', 'True') # 如果 'label' 不存在：默认返回 't'（表示“总为真”）
                # print(f'buchi_label ={buchi_label}')
                if match_buchi_label(buchi_label, label):
                    init_state = (x0, q)
                    # print(f'init_state ={init_state}')
                    Q0_product.add(init_state)
                    queue.append(init_state)
                    visited.add(init_state)
                    product.add_node(init_state)
    # 构建 δ⊗（仅保留访问得到的状态）
    while queue: #只要队列 queue 还有元素，就一直继续执行下面的循环体。
        (x, q) = queue.popleft()

        for x_succ in TS.successors(x):
            ts_edge_label = TS[x][x_succ].get('label', None)
            ts_edge_weight = TS[x][x_succ].get('weight', None)
            succ_ap_set = TS_labeling_func(TS, x_succ)

            for q_prime in Buchi.successors(q):
                buchi_label = Buchi[q][q_prime].get('label', 'True')
                if match_buchi_label(buchi_label, succ_ap_set):
                    next_product_state = (x_succ, q_prime)
                    product.add_node(next_product_state)
                    product.add_edge((x, q), next_product_state, label=ts_edge_label, weight= ts_edge_weight)
                    if next_product_state not in visited:
                        visited.add(next_product_state)
                        queue.append(next_product_state)

    # 接受状态 F⊗ = {(x, q) ∈ V_product | q ∈ Buchi_acc_states}
    F_product = set((x, q) for (x, q) in product.nodes if q in Buchi_acc_states)

    return product, Q0_product, F_product



def draw_product_automaton(product, initial_states=None, accepting_states=None):
    """
    绘制 Product Automaton，支持区分初始/接受/普通状态，标注边 label 和自环。
    """

    pos = nx.kamada_kawai_layout(product)  # 比 spring 更清晰一点（可换）
    pos = nx.spring_layout(product, seed=42, k=4.0)

    node_colors = []
    for node in product.nodes():
        if initial_states and node in initial_states and accepting_states and node in accepting_states:
            node_colors.append("yellow")  # 初始 + 接受
        elif initial_states and node in initial_states:
            node_colors.append("lightgreen")  # 初始状态
        elif accepting_states and node in accepting_states:
            node_colors.append("lightcoral")  # 接受状态
        else:
            node_colors.append("lightblue")  # 普通状态

    plt.figure(figsize=(12, 9))
    nx.draw(product, pos, with_labels=True, node_color=node_colors, node_size=1500, font_size=10, edgecolors='black')

    # 提取边的 label
    edge_labels = {(u, v): d.get("label", "") for u, v, d in product.edges(data=True)}

    # 正常边
    normal_edge_labels = {k: v for k, v in edge_labels.items() if k[0] != k[1]}
    nx.draw_networkx_edge_labels(product, pos, edge_labels=normal_edge_labels, font_color='red', font_size=9)

    # 自环标签单独画（避免重叠）
    loop_edges = {k: v for k, v in edge_labels.items() if k[0] == k[1]}
    for (u, _), label in loop_edges.items():
        x, y = pos[u]
        plt.text(x + 0.03, y + 0.08, label, fontsize=9, color='red', bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

    plt.title("Product Automaton", fontsize=14)
    plt.axis('off')
    # plt.tight_layout()
    plt.show()


if __name__ == "__main__":


    # test 1 GF a1
    filename = "output.ba"

    ap = {'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r', 'b', 'a1'}
    # +-----+-----+-----+
    # | r4,r| r5,b| r6,a|
    # +-----+-----+-----+
    # | r1,r| r2,b| r3,r|
    # +-----+-----+-----+

    regions = {
        (0, 0): {'r1', 'r'},
        (1, 0): {'r2', 'b'},
        (2, 0): {'r3', 'r'},
        (0, 1): {'r4', 'r'},
        (1, 1): {'r5', 'b'},
        (2, 1): {'r6', 'a1'},
    }

    edges = {
        ((0, 0), (1, 0)): ['u1', 1],
        ((1, 0), (2, 0)): ['u2', 2],
        ((0, 1), (1, 1)): ['u3', 3],
        ((1, 1), (2, 1)): ['u4', 4],
        ((0, 0), (0, 1)): ['u5', 5],
        ((1, 0), (1, 1)): ['u6', 6],
        ((2, 0), (2, 1)): ['u7', 7],
    }
    Buchi, Buchi_init_states, Buchi_acc_states = parse_custom_ba_with_multiple_states(filename)
    print(Buchi_init_states)
    print(Buchi.nodes(data=True))
    print(Buchi.edges(data=True))
    TS = build_region_graph(regions, edges)
    TS.nodes[(0, 0)]['init'] = True
    print(TS.nodes(data=True))
    print(TS.edges(data=True))
    result = match_buchi_label('!r1 & (r2 | r3)', {"r2","r3"})
    print(result)  # True

    product, Q0_product, product_accept = build_product_automaton_advance(TS, Buchi, Buchi_init_states, Buchi_acc_states)
    print(f'product = {product}')
    print(f'product node = {product.nodes(data=True)}')
    print(f'product edge = {product.edges(data=True)}')
    draw_product_automaton(product, Q0_product, product_accept)


    # test 2 yiwei's CDC
    filename = "yiwei_CDC.ba"

    ap = {'gather', 'upload', 'recharge', 'non'}

    regions = {
        'q0': {'non'},
        'q1': {'upload'},
        'q2': {'gather'},
        'q3': {'recharge'}
    }

    edges = {
        ('q0', 'q1'): ['u1', 1],
        ('q1', 'q0'): ['u1', 1],
        ('q0', 'q2'): ['u1', 1],
        ('q2', 'q3'): ['u1', 1],
        ('q3', 'q0'): ['u3', 1],
        ('q2', 'q1'): ['u2', 1],
    }
    Buchi, Buchi_init_states, Buchi_acc_states = parse_custom_ba_with_multiple_states(filename)
    Buchi_init_states = {'3'}
    TS = build_region_graph(regions, edges)
    TS.nodes['q0']['init'] = True
    product, Q0_product, product_accept = build_product_automaton_advance(TS, Buchi, Buchi_init_states,
                                                                          Buchi_acc_states)
    draw_product_automaton(product, Q0_product, product_accept)
