# Given values
pressure = 100  # kPa
diameter = 12    # mm
stress = 20000  # MPa
efficiency = 0.85

# Calculate the diameter of the pipe (mm)
pipe_diameter = diameter

# Calculate the thickness of the pipe wall (mm)
thickness_wall = (pressure * stress * efficiency) / (4 * 3.14159)

# Print the calculated thickness
print("The minimum pipe wall thickness is:", thickness_wall, "mm")