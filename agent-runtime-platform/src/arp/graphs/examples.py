from arp.graphs.engine import Graph, GraphState, Transition


async def prepare(state: GraphState) -> Transition:
    state["proposal"] = f"Review request: {state['goal']}"
    return Transition(next_node="publish", approval_required=True)


async def publish(state: GraphState) -> Transition:
    state["result"] = f"Approved: {state['proposal']}"
    return Transition()


def approval_graph() -> Graph:
    return Graph({"prepare": prepare, "publish": publish}, start="prepare")
