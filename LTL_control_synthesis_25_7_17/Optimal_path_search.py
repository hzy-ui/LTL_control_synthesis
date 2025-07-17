from Buchi_graph import *
from ts import *
import re
import networkx as nx
from Product import *



def find_min_prefix_suffix(product, Q0_product, product_accept):
    min_total_cost = float('inf')
    best_prefix = None
    best_suffix = None
    all_cycles = list(nx.simple_cycles(product))

    for init in Q0_product:
        # Step 1: 找 prefix（初始 -> 接收）
        try:
            prefix_lengths, prefix_paths = nx.single_source_dijkstra(product, init, weight='weight')
        except nx.NetworkXNoPath:
            continue

        for acc in product_accept:
            if acc not in prefix_paths:
                continue
            prefix_path = prefix_paths[acc]
            prefix_cost = prefix_lengths[acc]

            # Step 2: 找所有包含 acc 的环路，选代价最小的那个作为 suffix
            # all_cycles = list(nx.simple_cycles(product))
            acc_loops = [cycle for cycle in all_cycles if acc in cycle]

            best_loop = None
            best_loop_cost = float('inf')

            for loop in acc_loops:
                # 计算环路权重
                cost = 0
                for i in range(len(loop)):
                    u = loop[i]
                    v = loop[(i + 1) % len(loop)]
                    cost += product[u][v]['weight'] # 包括从最后一个节点回到第一个节点的边
                if cost < best_loop_cost:
                    best_loop_cost = cost
                    # 补全环路首尾
                    best_loop = loop + [loop[0]]

            if best_loop is None:
                # 没有找到合适的环路，跳过
                continue

            total_cost = prefix_cost + best_loop_cost

            if total_cost < min_total_cost:
                min_total_cost = total_cost
                best_prefix = prefix_path
                best_suffix = best_loop

    return best_prefix, best_suffix, min_total_cost


def extract_labels_from_path(graph, path):
    return [graph[path[i]][path[i+1]].get('label', None) for i in range(len(path) - 1)]
# def extract_labels_from_path(graph, path):
#     labels = []
#     for i in range(len(path) - 1):
#         u = path[i]
#         v = path[i + 1]
#         edge_data = graph[u][v]
#         # 如果是 MultiDiGraph（允许多边），取第一条
#         if isinstance(edge_data, dict) and 0 in edge_data:
#             label = edge_data[0].get('label', None)
#         else:
#             label = edge_data.get('label', None)
#         labels.append(label)
#     return labels

def combine_prefix_suffix_by_anchor(prefix, suffix):
    if not prefix or not suffix:
        return prefix

    # 去掉suffix首尾重复节点的最后一个
    if suffix[0] == suffix[-1]:
        suffix = suffix[:-1]

    anchor = prefix[-1]

    # 找到 suffix 中第一个 anchor 的位置
    try:
        anchor_idx = suffix.index(anchor)
    except ValueError:
        return prefix

    # 从 anchor 后一个开始，一直到再次遇到 anchor 为止（闭环一圈）
    loop = []
    i = (anchor_idx + 1) % len(suffix)
    while True:
        node = suffix[i]
        loop.append(node)
        # print(loop)
        if node == anchor:
            break
        i = (i + 1) % len(suffix)
        if i == anchor_idx + 1:
            # 没找到完整 loop，避免死循环
            break

    return prefix + loop

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

    best_prefix, best_suffix, min_total_cost = find_min_prefix_suffix(product, Q0_product, product_accept)
    print(f'best_prefix = {best_prefix}')
    print(f'best_suffix = {best_suffix}')
    print(f'min_total_cost = {min_total_cost}')
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
    Buchi_init_states = {'2'}
    TS = build_region_graph(regions, edges)
    TS.nodes['q0']['init'] = True
    product, Q0_product, product_accept = build_product_automaton_advance(TS, Buchi, Buchi_init_states,
                                                                          Buchi_acc_states)
    best_prefix, best_suffix, min_total_cost = find_min_prefix_suffix(product, Q0_product, product_accept)
    print(f'best_prefix = {best_prefix}')
    print(f'best_suffix = {best_suffix}')
    print(f'min_total_cost = {min_total_cost}')
    combined = combine_prefix_suffix_by_anchor(best_prefix, best_suffix)
    print(f'prefix-suffix structure = {combined}')
    run = extract_labels_from_path(product, combined)
    print(f'the controller sequence:{run}')
    draw_product_automaton(product, Q0_product, product_accept)
