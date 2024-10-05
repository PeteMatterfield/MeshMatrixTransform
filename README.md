# Mesh Matrix Transform
Python CLI application that aligns one mesh to another using iterative closest point.

# Why?

For technical artists and 3d scanning artists, often times you need to align two different meshes together for texture projection. Think high poly to low poly. If those two meshes have completely different transforms, your projection will fail. If you also do any structured light scanning paired with a photogrammetry solve for RGB, the two resulting meshes will not share the same world space position. This application allows you to match them up.

Note: great for automation pipelines!

# Usage
MeshMatrixTransform is a command line python application. Format is: meshmatrixtransform.py "mesh1" "mesh2" "matrixfile.npz" "process" "points"

"process" is the choice of process. Valid options are:
  * "-align" lets you create the transform matrix by plotting 6 markers and performing the ICP process. "mesh1" will be transformed to "mesh2" and the transform matrix will be saved to "matrixfile.npz"
  * "-apply" applies a matrix file "matrixfile.npz" to "mesh1" and outputs the transformed mesh to "mesh2"
  * "-reverse" applies the transform matrix in reverse to "mesh1" and outputs the transformed mesh to "mesh2"

You will typically start with: "matrixtransform.py "mesh1" "mesh2" "matrixfile" -align"

A split screen window pops up with each mesh loaded in a window.

![{D98F7A21-D6AF-412B-AF5A-D809C55C53E9}](https://github.com/user-attachments/assets/f31834de-53ae-4d41-9296-048f3dc6d815)

In the first window, hitting F2,F3, and F4 will plot red, green, and blue markers. In the second widnow, F5, F6, and F7 do the same. Place markers at roughly the same geographical location on each mesh. When ready, hitting the spacebar will begin the alignment process. The transformed mesh together with "mesh2" will render in the 3rd window. Behind the scenes, the transform matrix will be written to the "matrixfile" after the process has completed. Hitting the "export" button allows you to export the transformed mesh where you like.

![{6441E93E-63FF-448B-85FE-9A9E60497C92}](https://github.com/user-attachments/assets/12127f91-a327-41c4-8f5f-dd443c83b21c)

Hit "ESC" to quit.

# Other Options
The app downsamples the meshes into points and runs the ICP algorithms on those points. The default number of points is 200,000, but you can specify your own number of points using "-points x" command line argument where "x" is an integer. The higher the number, the longer the process will take, but the more accurate the alignment might be.

