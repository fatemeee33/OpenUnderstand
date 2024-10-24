import html

import graphviz as gv
import re
from cfg_generator.src.data_structures.graph.builder_interface import IDiGraphBuilder
from cfg_generator.src.antlr.rule_utils import extract_exact_text
from cfg_generator.src.graph.utils import head_node, last_node

FONT_SIZE = "22"
PEN_WIDTH = "2"


def draw_CFG(graph, end_nodes, filename, token_stream=None, format="png", verbose=True, function_name=None, output_list=None):
    if output_list is None:
        output_list = []  # Initialize the output list if not provided

    if graph.nodes:
        gr = gv.Digraph(comment=filename, format=format, node_attr={"shape": "none"})
        gr.node("start", style="filled", fillcolor="#aaffaa", shape="oval", fontsize=FONT_SIZE)

        # Create a dictionary to store the aggregated information for each basic node
        output_dict = {}

        # Loop through each node in the graph
        for node, data in graph.nodes.data():
            # Initialize or update the dictionary for the current node
            if node not in output_dict:
                output_dict[node] = {
                    "basic node id": node,  # Store the node id
                    "text": [],  # Store the text as a list
                    "node id": [],  # Store the integer ids as a list
                    "type": "Unknown",
                    "previous node": [],  # Store previous nodes (incoming edges)
                    "next node": [],
                    "function name": function_name  # Store the function name
                }

            # Check if 'value' exists in the data and is a non-empty list
            if 'value' in data and isinstance(data['value'], list) and data['value']:
                last_value = data['value'][-1]  # Get the last value
                # Extract the class name using type() and __name__
                output_dict[node]["type"] = type(last_value).__name__  # Get the class name without the memory address
            else:
                output_dict[node]["type"] = "Unknown"  # If 'value' is missing or empty

            # Get block contents (stringified) using the appropriate method
            block_contents = (stringify_block(data, token_stream) if verbose else stringify_block_lineno_only(data))

            # Use regex to find integer ids and associated text from block contents
            matches = re.findall(r'(\d+):\s*([^<]+)', block_contents)

            # Loop through the matches (integer id and text)
            for integer_id, text in matches:
                # Append the text and node id to the lists if not already present
                if integer_id not in output_dict[node]["node id"]:
                    output_dict[node]["node id"].append(integer_id)

                if text.strip() not in output_dict[node]["text"]:
                    output_dict[node]["text"].append(text.strip())

            # Assuming you're using the node for graph visualization as well
            gr.node(str(node), label=build_node_template(node, block_contents))

        gr.node("end", style="filled", fillcolor="#aaffaa", shape="oval", fontsize=FONT_SIZE)
        for f, t, data in graph.edges.data():
            # Add the "next node" (successor) to the current node f
            if t not in output_dict[f]["next node"]:
                output_dict[f]["next node"].append(t)

            # Add the "previous node" (predecessor) to the target node t
            if f not in output_dict[t]["previous node"]:
                output_dict[t]["previous node"].append(f)
                gr.edge(f"{str(f)}", f"{str(t)}", label=data["value"] if data else '', fontsize=FONT_SIZE,
                        penwidth=PEN_WIDTH)

        # Convert the dictionary to a list of dictionaries and append to the output_list
        output_list.extend(output_dict.values())

        gr.edge("start", str(head_node(graph)) if len(graph.nodes) > 0 else "end", penwidth=PEN_WIDTH)

        if end_nodes:
            for end in end_nodes:
                gr.edge(str(end[0]), "end", penwidth=PEN_WIDTH, label=end[1])
        else:
            gr.edge(str(last_node(graph)), "end", penwidth=PEN_WIDTH)

        gr.render(f"{filename}-cfg.gv", view=False)

def build_node_template(node_label, contents):
    b_len = len(contents.splitlines())
    line_height = 40
    s = f"""<<FONT POINT-SIZE="{FONT_SIZE}">  
        <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">
            <tr>
                <td width="50" height="50" fixedsize="true">{node_label + 1}</td>
                <td width="9" height="9" fixedsize="true" style="invis"></td>
                <td width="9" height="9" fixedsize="true" style="invis"></td>
            </tr>
            <tr>
                <td width="50" height="{b_len * line_height}" fixedsize="true" sides="tlb"></td>
                <td width="50" height="{b_len * line_height}" fixedsize="false" sides="bt" PORT="here">{contents}</td>
                <td width="50" height="{b_len * line_height}" fixedsize="true" sides="brt"></td>
            </tr>
        </TABLE>
    </FONT>>"""
    return strip_lines(s)


def strip_lines(x: str): return "\n".join(line.strip() for line in x.splitlines())


def node_content_to_html(node_contents):
    delimiter = '<br align="left"/>\n'
    content_list_string = delimiter.join([html.escape(f"{l}: {content}") for l, content in node_contents])
    # print(content_list_string + delimiter)
    return content_list_string + delimiter


def stringify_block(node_args, token_stream):
    if node_args == {}:
        return ""
    else:
        cs = [(rule.start.line, extract_exact_text(token_stream, rule)) for rule in node_args["value"]]
        b = node_content_to_html(cs)
        # print(b)
        return b


def stringify_block_lineno_only(node_args):
    data = node_args["value"]
    left, right = data[0].start.line, data[-1].stop.line
    if left == right:
        return f"{left}"

    return f"{left}..{right}"
