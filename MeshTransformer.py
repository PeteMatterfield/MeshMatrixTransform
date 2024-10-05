import numpy as np
from vedo import Mesh

class MeshTransformer:
    def __init__(self):
        self.initial_transform = None
        self.icp_transform = None
    def savePoints(self, points, filename="transform_markers.npz"):
        print("Saving Marker File")        
        data = []
        for index,marker in points.items():
            data.append(marker.pos())
        np.savez(filename, points=data)
        print("Saved User Created Points")
    def loadPoints(self,filename="transform_markers.npz"):
        print("Loading Marker File")
        data = np.load(filename)
        points = data['points']
        return points
    def save_transform_matrices(self, initial_transform, icp_transform, filename="transform_matrices.npz"):
        """Save both initial and ICP transformation matrices."""
        self.initial_transform = initial_transform
        self.icp_transform = icp_transform
        np.savez(filename, initial=initial_transform, icp=icp_transform)
        print(f"Transform matrices saved to {filename}")

    def load_transform_matrices(self, filename="transform_matrices.npz"):
        """Load both initial and ICP transformation matrices."""
        data = np.load(filename)
        self.initial_transform = data['initial']
        self.icp_transform = data['icp']
        print(f"Transform matrices loaded from {filename}")
        return self.initial_transform, self.icp_transform

    def apply_forward_transform(self, mesh):
        """Apply the forward transformation to the given mesh."""
        if self.initial_transform is None or self.icp_transform is None:
            raise ValueError("Transform matrices not loaded. Call load_transform_matrices() first.")
        mesh.apply_transform(self.initial_transform)
        mesh.apply_transform(self.icp_transform)
        return mesh

    def apply_inverse_transform(self, mesh):
        """Apply the inverse transformation to the given mesh."""
        if self.initial_transform is None or self.icp_transform is None:
            raise ValueError("Transform matrices not loaded. Call load_transform_matrices() first.")
        # First, apply inverse of ICP transform
        inverse_icp = np.linalg.inv(self.icp_transform)
        mesh.apply_transform(inverse_icp)
        # Then, apply inverse of initial transform
        inverse_initial = np.linalg.inv(self.initial_transform)
        mesh.apply_transform(inverse_initial)
        return mesh

    def save_mesh(self, mesh, filename="transformed_mesh.obj"):
        print("Saving Mesh..")
        """Save the mesh to disk."""
        mesh.write(filename)
        print(f"Mesh saved to {filename}")