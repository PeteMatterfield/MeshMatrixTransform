import argparse
from vedo import Plotter, load, Point, Text2D,Button
import numpy as np
from scipy.spatial import cKDTree
from MeshTransformer import MeshTransformer
import os
import tkinter as tk
from tkinter import filedialog
class MeshViewer:
    def __init__(self, mesh1_file, mesh2_file, transform_file, numpoints):
        self.plt = Plotter(N=3, shape="1|2", bg='black', title="3D Mesh Viewer", sharecam=False)
        self.mesh1_file = mesh1_file
        self.mesh2_file = mesh2_file        
        self.transform_file = transform_file
        self.numpoints = numpoints
        self.load_meshes()

        self.markers = {}
        self.colors = ["red", "green", "blue"]
        self.instructions1 = Text2D("F2-F4 to place markers\nPress SPACE to align meshes", pos="top-left", c="white", s=0.8)
        self.instructions2 = Text2D("F5-F7 to place markers\nPress SPACE to align meshes", pos="top-left", c="white", s=0.8)
        self.plt.at(0).add(self.instructions1)
        self.plt.at(1).add(self.instructions2)

        self.max_iterations = 50
        self.tolerance = 1e-6
        
        dirTransform = os.path.dirname(transform_file)
        self.markerFile = os.path.join(dirTransform, "transform_markers.npz")
        if os.path.isfile(self.markerFile):
            print("Marker file found. Loading.")
            transformer = MeshTransformer()
            markerPositions = transformer.loadPoints(self.markerFile)            
            self.init_points(markerPositions)

        self.progress_text = None
        self.export_button = None
        self.aligned_mesh = None
        
    def load_meshes(self):
        self.mesh1 = load(self.mesh1_file).lighting('plastic').color("lightblue")
        self.mesh2 = load(self.mesh2_file).lighting('plastic').color("gray")
        self.plt.at(0).add(self.mesh1).reset_camera()
        self.plt.at(1).add(self.mesh2).reset_camera()

    def init_points(self, markerPositions):
        for i, point in enumerate(markerPositions):
            color = self.colors[i % 3]
            marker = Point(point, c=color, r=15)
            self.markers[i] = marker
            if i < 3:
                self.plt.at(0).add(marker)
            else:
                self.plt.at(1).add(marker)
            print(f"Added/Updated point at {point} with color {color}")

    def calculate_transform(self, points1, points2):
        centroid1 = np.mean(points1, axis=0)
        centroid2 = np.mean(points2, axis=0)
        centered1 = points1 - centroid1
        centered2 = points2 - centroid2

        scale = np.sqrt(np.sum(centered2**2) / np.sum(centered1**2))
        H = centered1.T @ centered2
        U, _, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T

        if np.linalg.det(R) < 0:
            Vt[-1,:] *= -1
            R = Vt.T @ U.T

        t = centroid2 - scale * (R @ centroid1)

        transform = np.eye(4)
        transform[:3, :3] = scale * R
        transform[:3, 3] = t

        return transform

    def apply_transform_to_points(self, points, transform):
        points_homogeneous = np.column_stack((points, np.ones(len(points))))
        transformed_points = (transform @ points_homogeneous.T).T
        return transformed_points[:, :3] / transformed_points[:, 3:]

    def downsample_points(self, points, target_count):
        if len(points) <= target_count:
            return points
        indices = np.random.choice(len(points), target_count, replace=False)
        return points[indices]

    def icp_align(self, source_points, target_points, initial_transform, max_iterations=50, tolerance=1e-6):
        transform = initial_transform
        target_tree = cKDTree(target_points)

        for i in range(max_iterations):
            source_transformed = self.apply_transform_to_points(source_points, transform)
            distances, indices = target_tree.query(source_transformed)
            new_transform = self.calculate_transform(source_transformed, target_points[indices])
            transform = new_transform @ transform

            # Update progress text
            progress = (i + 1) / max_iterations
            self.progress_text.text(f"ICP Alignment Progress: {progress:.0%}")
            self.plt.render()

            if np.mean(distances) < tolerance:
                break

        aligned_source_points = self.apply_transform_to_points(source_points, transform)
        return transform, aligned_source_points

    def calculate_alignment_error(self, source_points, target_points, transformed_source_points):
        target_tree = cKDTree(target_points)
        distances, _ = target_tree.query(transformed_source_points)
        average_distance = np.mean(distances)
        rmse = np.sqrt(np.mean(np.square(distances)))
        hausdorff_distance = np.max(distances)

        return {
            "average_distance": average_distance,
            "rmse": rmse,
            "hausdorff_distance": hausdorff_distance
        }

    def align_meshes(self):
        if len(self.markers) != 6:
            print(f"Please place all 6 markers before aligning. Current markers: {len(self.markers)}")
            return

        transformer = MeshTransformer()
        transformer.savePoints(self.markers, self.markerFile)
        
        points1 = np.array([self.markers[i].pos() for i in range(3)])
        points2 = np.array([self.markers[i].pos() for i in range(3, 6)])

        initial_transform = self.calculate_transform(points1, points2)
        transformed_mesh1 = self.mesh1.clone().apply_transform(initial_transform)

        target_point_count = min(self.numpoints, len(self.mesh1.points()))
        source_points = self.downsample_points(np.array(transformed_mesh1.points()), target_point_count)
        target_points = self.downsample_points(np.array(self.mesh2.points()), target_point_count)

        # Create progress text
        self.progress_text = Text2D("ICP Alignment Progress: 0%", pos=(0.05, 0.05), c="yellow", s=0.8)
        self.plt.at(2).add(self.progress_text)

        icp_transform, aligned_source_points = self.icp_align(source_points, target_points, np.eye(4))
        self.plt.at(2).remove(self.progress_text)
        final_transform = icp_transform @ initial_transform
        self.aligned_mesh = self.mesh1.clone().apply_transform(final_transform)

        error_metrics = self.calculate_alignment_error(source_points, target_points, aligned_source_points)

        self.plt.at(2).clear()
        self.plt.at(2).add(self.mesh2)
        self.plt.at(2).add(self.aligned_mesh).reset_camera()
        self.plt.at(2).add(Text2D("Aligned Meshes", pos=(0.05, 0.95), c="white", s=0.8))
        
        error_text = (f"Alignment Error Metrics:\n"
                      f"Average Distance: {error_metrics['average_distance']:.4f}\n"
                      f"RMSE: {error_metrics['rmse']:.4f}\n"
                      f"Hausdorff Distance: {error_metrics['hausdorff_distance']:.4f}")
        self.plt.at(2).add(Text2D(error_text, pos=(0.05, 0.15), c="yellow", s=0.6))

        transformer.save_transform_matrices(initial_transform, icp_transform, self.transform_file)
        transformer.savePoints(self.markers, self.markerFile)
        
        # Add export button
        self.export_button = Button(self.export_mesh, pos=(0.85, 0.05), c="blue", bc="lightblue", size=12, states=["Export"])
        self.plt.at(2).add(self.export_button)
        self.plt.at(2).add_callback("LeftButtonPress", self.on_click)
        self.plt.render()
    
    def on_click(self, evt):
        if evt.actor == self.export_button:
            self.export_mesh()
            
    def add_marker(self, evt):
        if evt.keypress in ["F2", "F3", "F4", "F5", "F6", "F7"]:
            point = evt.picked3d
            if point is None:
                return
            
            # Determine which mesh was clicked
            if evt.actor == self.mesh1:
                plotter_index = 0
                valid_keys = ["F2", "F3", "F4"]
            elif evt.actor == self.mesh2:
                plotter_index = 1
                valid_keys = ["F5", "F6", "F7"]
            else:
                print("No mesh was clicked.")
                return
            
            if evt.keypress not in valid_keys:
                print(f"Invalid key {evt.keypress} for plotter {plotter_index}")
                return
            
            index = valid_keys.index(evt.keypress) + (3 if plotter_index == 1 else 0)
            color = self.colors[index % 3]
            
            if index in self.markers:
                self.plt.at(plotter_index).remove(self.markers[index])
            
            marker = Point(point, c=color, r=15)
            self.markers[index] = marker
            self.plt.at(plotter_index).add(marker)
            print(f"Added/Updated point at {point} with color {color} in plotter {plotter_index}")
    
    
    def export_mesh(self):
        
        if self.aligned_mesh is None:
            print("No aligned mesh to export.")
            return

        root = tk.Tk()
        root.withdraw()  # Hide the main window
        file_path = filedialog.asksaveasfilename(defaultextension=".obj",
                                                 filetypes=[("OBJ files", "*.obj"), ("All files", "*.*")])
        if file_path:
            self.aligned_mesh.write(file_path)
            print(f"Aligned mesh exported to {file_path}")
    
            
    def key_pressed(self, evt):
        key = evt.keypress
        #print(f"Key pressed: {key}")
        
        if key == 'space':
            self.align_meshes()
        elif key in ['F2', 'F3', 'F4', 'F5', 'F6', 'F7']:
            self.add_marker(evt)
        
        self.plt.render()
        
    def run(self):
        self.plt.add_callback('KeyPress', self.key_pressed)
        self.plt.show().interactive()

def main():
    parser = argparse.ArgumentParser(description="Process Meshes with options.")
    parser.add_argument("meshfile1", type=str, help="First mesh file to process.")
    parser.add_argument("meshfile2", type=str, help="Second mesh file to process.")
    parser.add_argument("transformfile", type=str, help="File to save/load transformation matrices in npz format.")
    parser.add_argument("-align", action="store_true", help="Align mesh1 to mesh2 using a GUI. This outputs transformation matrices to the specified file.")
    parser.add_argument("-reverse", action="store_true", help="Applies the inverse transformation from the specified file to meshfile1.")
    parser.add_argument("-apply", action="store_true", help="Applies the transformation from the specified file to meshfile1.")
    parser.add_argument("-points", type=int, required=False, default=200000, help="Number of points to use to calculate alignment.")
    args = parser.parse_args()

    if args.align:
        viewer = MeshViewer(args.meshfile1, args.meshfile2, args.transformfile, args.points)
        viewer.run()
    elif args.reverse or args.apply:
        transformer = MeshTransformer()
        initial_transform, icp_transform = transformer.load_transform_matrices(args.transformfile)
        mesh1 = load(args.meshfile1)
        if args.reverse:
            mesh1 = transformer.apply_inverse_transform(mesh1)
        else:
            mesh1 = transformer.apply_forward_transform(mesh1)
        transformer.save_mesh(mesh1, args.meshfile2)
        print(f"{'Inverse' if args.reverse else 'Forward'} transformation applied and saved to '{args.meshfile2}'")
    else:
        print("Please specify either -align, -reverse, or -apply option.")

if __name__ == "__main__":
    main()