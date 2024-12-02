import tkinter as tk
from tkinter import filedialog, messagebox
import json
import heapq

class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Graph Builder with Pathfinding and Save/Load")
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.control_frame = tk.Frame(root, bg="lightgray")
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.add_controls()

        self.nodes = []
        self.edges = {}
        self.selected_node = None
        self.path_nodes = []

    def add_controls(self):
        tk.Button(self.control_frame, text="Clear Graph", command=self.clear_graph, bg="red", fg="white").pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Save Graph", command=self.save_graph, bg="green", fg="white").pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Load Graph", command=self.load_graph, bg="orange", fg="white").pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.control_frame, text="Find Path", command=self.find_path, bg="blue", fg="white").pack(side=tk.LEFT, padx=5, pady=5)
        tk.Label(self.control_frame, text="Click to add nodes. Right-click to connect nodes.", bg="lightgray").pack(side=tk.LEFT, padx=10)

    def clear_graph(self):
        self.canvas.delete("all")
        self.nodes = []
        self.edges = {}
        self.selected_node = None
        self.path_nodes = []

    def add_node(self, event):
        x, y = event.x, event.y
        node_id = len(self.nodes) + 1
        self.nodes.append((x, y, node_id))
        self.edges[node_id] = []
        self.canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill="skyblue", outline="black", width=2, tags=f"node_{node_id}")
        self.canvas.create_text(x, y, text=str(node_id), font=("Arial", 12, "bold"))

    def connect_nodes(self, event):
        clicked_item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(clicked_item)
        if not tags or "node_" not in tags[0]:
            return

        node_tag = tags[0]
        node_index = int(node_tag.split("_")[1]) - 1

        if self.selected_node is None:
            self.selected_node = node_index
            self.highlight_node(self.nodes[node_index])
        else:
            x1, y1, id1 = self.nodes[self.selected_node]
            x2, y2, id2 = self.nodes[node_index]
            weight = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5  # Euclidean distance as weight
            self.edges[id1].append((id2, weight))
            self.edges[id2].append((id1, weight))
            self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
            self.unhighlight_node(self.nodes[self.selected_node])
            self.selected_node = None

    def highlight_node(self, node):
        x, y, node_id = node
        self.canvas.create_oval(x - 17, y - 17, x + 17, y + 17, outline="red", width=2, tags=f"highlight_{node_id}")

    def unhighlight_node(self, node):
        _, _, node_id = node
        self.canvas.delete(f"highlight_{node_id}")

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.add_node)   # Left-click to add node
        self.canvas.bind("<Button-3>", self.connect_nodes)  # Right-click to connect nodes

    def find_path(self):
        if len(self.nodes) < 2:
            messagebox.showinfo("Pathfinding Error", "Not enough nodes to find a path.")
            return

        start = tk.simpledialog.askinteger("Pathfinding", "Enter the start node ID:")
        end = tk.simpledialog.askinteger("Pathfinding", "Enter the end node ID:")

        if start not in self.edges or end not in self.edges:
            messagebox.showinfo("Pathfinding Error", "Invalid node IDs.")
            return

        path, distance = self.dijkstra(start, end)
        if not path:
            messagebox.showinfo("Pathfinding Result", "No path found.")
        else:
            self.highlight_path(path)
            messagebox.showinfo("Pathfinding Result", f"Path: {' -> '.join(map(str, path))}\nDistance: {distance:.2f}")

    def dijkstra(self, start, end):
        distances = {node: float('inf') for node in self.edges}
        distances[start] = 0
        prev_nodes = {node: None for node in self.edges}
        pq = [(0, start)]

        while pq:
            current_distance, current_node = heapq.heappop(pq)

            if current_distance > distances[current_node]:
                continue

            for neighbor, weight in self.edges[current_node]:
                distance = current_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    prev_nodes[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))

        path = []
        current = end
        while current is not None:
            path.insert(0, current)
            current = prev_nodes[current]

        if distances[end] == float('inf'):
            return None, None

        return path, distances[end]

    def highlight_path(self, path):
        self.canvas.delete("path")
        for i in range(len(path) - 1):
            x1, y1, _ = self.nodes[path[i] - 1]
            x2, y2, _ = self.nodes[path[i + 1] - 1]
            self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=3, tags="path")

    def save_graph(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        graph_data = {
            "nodes": [{"id": node_id, "x": x, "y": y} for x, y, node_id in self.nodes],
            "edges": {node: edges for node, edges in self.edges.items()}
        }

        with open(file_path, "w") as file:
            json.dump(graph_data, file, indent=4)

        messagebox.showinfo("Save Graph", f"Graph saved to {file_path}.")

    def load_graph(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        with open(file_path, "r") as file:
            graph_data = json.load(file)

        self.clear_graph()
        for node in graph_data["nodes"]:
            self.nodes.append((node["x"], node["y"], node["id"]))
            self.edges[node["id"]] = []

        for node_id, edges in graph_data["edges"].items():
            self.edges[int(node_id)] = [(e[0], e[1]) for e in edges]

        self.redraw_graph()

    def redraw_graph(self):
        for x, y, node_id in self.nodes:
            self.canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill="skyblue", outline="black", width=2, tags=f"node_{node_id}")
            self.canvas.create_text(x, y, text=str(node_id), font=("Arial", 12, "bold"))

        for node_id, edges in self.edges.items():
            x1, y1, _ = self.nodes[node_id - 1]
            for neighbor, _ in edges:
                x2, y2, _ = self.nodes[neighbor - 1]
                self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)

def main():
    root = tk.Tk()
    app = GraphApp(root)
    app.bind_events()
    root.mainloop()

if __name__ == "__main__":
    main()
