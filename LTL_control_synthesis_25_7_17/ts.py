# ap = {'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r', 'b'}
# # +-----+-----+-----+
# # | r4,r| r5,b| r6,b|
# # +-----+-----+-----+
# # | r1,r| r2,b| r3,r|
# # +-----+-----+-----+
# regions = {   (0, 0, 1): set(['r1', 'r']),
#               (1, 0, 1): set(['r2', 'b']),
#               (2, 0, 1): set(['r3', 'r']),
#               (0, 1, 1): set(['r4', 'r']),
#               (1, 1, 1): set(['r5', 'b']),
#               (2, 1, 1): set(['r6', 'b']),
# }
#
# u = {'u1', 'u2', 'u3', 'u4', 'u5', 'u6', 'u7'}
#
# edges = {((0, 0, 1), (1, 0, 1)): ['u1', 1],
#          ((1, 0, 1), (2, 0, 1)): ['u2', 2],
#          ((0, 1, 1), (1, 1, 1)): ['u3', 3],
#          ((1, 1, 1), (2, 1, 1)): ['u4', 4],
#          ((0, 0, 1), (0, 1, 1)): ['u5', 5],
#          ((1, 0, 1), (1, 1, 1)): ['u6', 6],
#          ((2, 0, 1), (2, 1, 1)): ['u7', 7],
#          }
# 我想通过上面这些数据建立一个状态转移系统， 转移关系在edges中，转移的label和权重对应后面的 例如['u1', 1]，region的label是ap 例如 (0, 0, 1): set(['r1', 'r'])，请基于networkx构建 最后再画出来

import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

def build_region_graph(regions, edges):
    """
    构建区域状态转移图（带AP和动作标签）

    参数:
        regions: dict[tuple, set]，每个节点的位置 -> AP标签集合
        edges: dict[tuple(tuple, tuple), list]，转移边 (from, to) -> [动作, 权重]

    返回:
        G: networkx.DiGraph 对象，节点含'ap'属性，边含'label'和'weight'
    """
    G = nx.DiGraph()

    # 添加节点和AP标签
    for state, aps in regions.items():
        G.add_node(state, ap=aps)

    # 添加边和动作/权重
    for (src, dst), (action, weight) in edges.items():
        G.add_edge(src, dst, label=action, weight=weight)

    return G


def draw_region_graph(G, layout='spring'):
    """
    绘制状态转移图，包括AP标签、动作/权重标签

    参数:
        G: networkx.DiGraph，图对象
        layout: str，布局方式（可选 'spring' 或 'kamada'）
    """
    # 选择布局
    if layout == 'kamada':
        try:
            pos = nx.kamada_kawai_layout(G)
        except ImportError:
            print("Kamada-Kawai layout 需要 scipy 支持，已退回 spring_layout")
            pos = nx.spring_layout(G, seed=42)
    else:
        pos = nx.spring_layout(G, seed=42)

    # 构建节点标签（显示为逗号分隔的AP）
    node_labels = {n: ','.join(sorted(G.nodes[n]['ap'])) for n in G.nodes}
    node_labels = {n: f"{n}: " + ','.join(sorted(G.nodes[n]['ap'])) for n in G.nodes}

    # 构建边标签（显示为 动作 / 权重）
    edge_labels = {(u, v): f"{d['label']} / {d['weight']}" for u, v, d in G.edges(data=True)}

    # 绘制图
    plt.figure(figsize=(10, 7))
    nx.draw(G, pos, with_labels=False, node_size=1500, node_color='lightblue', edge_color='gray', arrows=True)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=9)

    plt.title("Region Transition Graph")
    plt.axis('off')
    # plt.tight_layout()
    plt.show()


ap = {'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r', 'b'}
# +-----+-----+-----+
# | r4,r| r5,b| r6,a|
# +-----+-----+-----+
# | r1,r| r2,b| r3,r|
# +-----+-----+-----+

regions = {
    (0, 0, 1): {'r1', 'r'},
    (1, 0, 1): {'r2', 'b'},
    (2, 0, 1): {'r3', 'r'},
    (0, 1, 1): {'r4', 'r'},
    (1, 1, 1): {'r5', 'b'},
    (2, 1, 1): {'r6', 'a'},
}

edges = {
    ((0, 0, 1), (1, 0, 1)): ['u1', 1],
    ((1, 0, 1), (2, 0, 1)): ['u2', 2],
    ((0, 1, 1), (1, 1, 1)): ['u3', 3],
    ((1, 1, 1), (2, 1, 1)): ['u4', 4],
    ((0, 0, 1), (0, 1, 1)): ['u5', 5],
    ((1, 0, 1), (1, 1, 1)): ['u6', 6],
    ((2, 0, 1), (2, 1, 1)): ['u7', 7],
}

if __name__ == "__main__":
    # === 构建图并绘图 ===
    G = build_region_graph(regions, edges)
    draw_region_graph(G)