import math
import uuid

# Function for calculating int length of line segment
# Args: 2 Tuples p1 & p2 in format (x, y)
def lnseg_distance(p1, p2):
    """
    Calculate the distance between two points
    Point format: tuple, (x, y)
    """
    
    return int(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))

# Return point coord tuple of rotated point
def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in degrees.
    """
    # Convert angle to radians
    angle = angle * 0.0174533

    ox, oy = origin
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return int(qx), int(qy)

def set_hash_val():
  # Generate hash and turn to string
  hash_val = str(uuid.uuid1())
  # Return hash string
  return hash_val

def int_hypotenuse(height, width):
    """
    Calculates the integer hypotenuse from height and width of triangle
    """
    return math.isqrt((height ** 2) + (width ** 2))

def update_val(val, input_val):

  if (val != input_val):
    return input_val
  else:
    return val